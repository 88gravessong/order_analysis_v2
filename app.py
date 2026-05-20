#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py
简单的 Flask Web 应用：
1. 首页提供多文件上传和日期范围选择（精确到日）。
2. POST /process 接收文件与日期范围，调用 compute_logic.compute_metrics。
3. 返回生成的 Excel 文件供下载。
"""

from datetime import datetime, date
from io import BytesIO
import os
import uuid
from tempfile import gettempdir

from flask import (
    Flask,
    render_template,
    request,
    send_file,
    flash,
    redirect,
    url_for,
    session,
)
from werkzeug.utils import secure_filename

from compute_logic import compute_metrics
from metrics_core import metric_rates

from compute_province_metrics import compute_metrics_streams, build_result_workbook as build_province_workbook
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-me")
UPLOAD_DIR = os.path.join(gettempdir(), "order_analysis_uploads")
RESULT_DIR = os.path.join(gettempdir(), "order_analysis_results")
ALLOWED_EXTENSIONS = {".xlsx", ".csv"}


def _ensure_temp_dirs():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(RESULT_DIR, exist_ok=True)


def _upload_path(file_id, filename):
    return os.path.join(UPLOAD_DIR, f"{file_id}_{filename}")


def _upload_item_path(item):
    if item.get("id"):
        return _upload_path(item["id"], item["name"])
    return item.get("path")


def _result_path(filename):
    return os.path.join(RESULT_DIR, filename)


def _is_allowed_upload(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


def _load_saved_uploads():
    return session.get("uploaded_files", [])


def _public_saved_uploads():
    return [{"name": item.get("name", "")} for item in _load_saved_uploads()]


def _save_request_uploads(files):
    _ensure_temp_dirs()
    saved = _load_saved_uploads()
    for f in files:
        if not f.filename:
            continue
        filename = secure_filename(f.filename)
        if not filename or not _is_allowed_upload(filename):
            raise ValueError(f"不支持的文件格式: {f.filename}")
        if any(item["name"] == filename for item in saved):
            continue
        file_id = uuid.uuid4().hex
        f.save(_upload_path(file_id, filename))
        saved.append({"name": filename, "id": file_id})
    session["uploaded_files"] = saved
    return saved


def _get_uploads_from_request():
    files = request.files.getlist("files") if "files" in request.files else []
    if files and files[0].filename != "":
        return _save_request_uploads(files)
    saved = _load_saved_uploads()
    if not saved:
        raise ValueError("请至少上传一个文件！")
    return saved


def _parse_date_range():
    start_str = request.form.get("start_date")
    end_str = request.form.get("end_date")
    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date() if start_str else date.min
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date() if end_str else date.max
    except ValueError:
        raise ValueError("日期格式错误，应为 YYYY-MM-DD")
    if start_date > end_date:
        raise ValueError("开始日期不能晚于结束日期！")
    return start_date, end_date


def _open_upload_streams(saved):
    file_streams = []
    for item in saved:
        path = _upload_item_path(item)
        if not path or not os.path.exists(path):
            raise FileNotFoundError(f"已保存文件不存在或已过期: {item['name']}")
        with open(path, "rb") as f:
            file_streams.append(BytesIO(f.read()))
    return file_streams


def _save_workbook(wb, prefix):
    _ensure_temp_dirs()
    temp_filename = f"{prefix}_{uuid.uuid4().hex[:8]}.xlsx"
    wb.save(_result_path(temp_filename))
    return temp_filename


def _summary_rows(stats):
    results_data = []
    for sku, metrics in sorted(stats.items(), key=lambda x: (-x[1]["total"], x[0])):
        total = metrics["total"]
        if total == 0:
            continue
        row = {
            "seller_sku": sku,
            "total": total,
        }
        row.update(metric_rates(metrics, total))
        results_data.append(row)
    return results_data


def _province_rows(stats, sku_totals):
    province_results = []
    for sku, prov_map in sorted(stats.items(), key=lambda x: x[0]):
        total_sku = sku_totals.get(sku, 0)
        for prov, metrics in sorted(prov_map.items(), key=lambda x: (-x[1]["total"], x[0])):
            total = metrics["total"]
            row = {
                "seller_sku": sku,
                "province": prov,
                "total": total,
                "share_rate": round(total / total_sku * 100, 2) if total_sku else 0,
            }
            row.update(metric_rates(metrics, total))
            province_results.append(row)
    return province_results


@app.route("/")
def index():
    # 从session获取已保存文件，在会话期间保持
    saved_files = _public_saved_uploads()
    return render_template("index.html", saved_files=saved_files)


@app.route("/process", methods=["POST"])
def process():
    try:
        saved = _get_uploads_from_request()
        start_date, end_date = _parse_date_range()
        file_streams = _open_upload_streams(saved)
    except ValueError as e:
        flash(str(e))
        return redirect(url_for("index"))
    except Exception as e:
        flash(str(e))
        return redirect(url_for("index"))

    try:
        wb, stats = compute_metrics(file_streams, start_date, end_date)
        if not stats:
            flash("在所选日期范围内未找到符合条件的数据，请调整日期或检查文件！")
            return redirect(url_for("index"))
    except Exception as e:
        flash(f"处理文件时发生错误: {e}")
        return redirect(url_for("index"))

    temp_filename = _save_workbook(wb, "order_metrics")
    results_data = _summary_rows(stats)
    
    return render_template(
        "results.html",
        results=results_data,
        sku_count=len(results_data),
        start_date=start_date,
        end_date=end_date,
        temp_filename=temp_filename,
        total_files=len(saved),
        total_orders=sum(r['total'] for r in results_data),
        sku_options=[],
    )


@app.route("/process_province", methods=["POST"])
def process_province():
    try:
        saved = _get_uploads_from_request()
        start_date, end_date = _parse_date_range()
        file_streams = _open_upload_streams(saved)
    except ValueError as e:
        flash(str(e))
        return redirect(url_for("index"))
    except Exception as e:
        flash(str(e))
        return redirect(url_for("index"))

    try:
        stats, sku_totals = compute_metrics_streams(file_streams, start_date, end_date)
        if not stats:
            flash("在所选日期范围内未找到符合条件的数据，请调整日期或检查文件！")
            return redirect(url_for("index"))
        wb = build_province_workbook(stats, sku_totals)
    except Exception as e:
        flash(f"处理文件时发生错误: {e}")
        return redirect(url_for("index"))

    temp_filename = _save_workbook(wb, "province_metrics")
    province_results = _province_rows(stats, sku_totals)

    total_orders = sum(r['total'] for r in province_results)
    sku_count = len(stats)
    sku_options = [
        sku for sku, _ in sorted(sku_totals.items(), key=lambda x: (-x[1], x[0]))
    ]

    return render_template(
        "results.html",
        province_results=province_results,
        results=[],
        sku_count=sku_count,
        start_date=start_date,
        end_date=end_date,
        temp_filename=temp_filename,
        total_files=len(saved),
        total_orders=total_orders,
        sku_options=sku_options,
    )


@app.route("/download/<filename>")
def download(filename):
    """下载临时生成的结果文件"""
    if not filename.startswith(("order_metrics_", "province_metrics_")) or "/" in filename:
        flash("下载文件名无效！")
        return redirect(url_for("index"))
    temp_path = _result_path(filename)
    if not os.path.exists(temp_path):
        flash("文件不存在或已过期！")
        return redirect(url_for("index"))

    with open(temp_path, "rb") as f:
        output = BytesIO(f.read())
    output.seek(0)
    try:
        os.remove(temp_path)
    except OSError:
        pass

    return send_file(
        output,
        as_attachment=True,
        download_name=f"订单指标分析结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/clear_files", methods=["POST"])
def clear_files():
    """清除session中保存的所有文件"""
    saved_files = session.get("uploaded_files", [])
    
    # 删除临时文件
    for item in saved_files:
        try:
            path = _upload_item_path(item)
            if path and os.path.exists(path):
                os.remove(path)
        except OSError:
            pass
    
    # 清空session
    session.pop("uploaded_files", None)
    flash("已清除所有上传文件！")
    return redirect(url_for("index"))


if __name__ == "__main__":
    # 在本地测试使用，部署时请使用 WSGI Server
    port = int(os.environ.get("PORT", "4004"))
    debug = os.environ.get("FLASK_DEBUG", "1") != "0"
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=False)

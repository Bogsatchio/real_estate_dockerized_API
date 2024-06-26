import os
import traceback
import pandas as pd
import tempfile
import json
import shutil
from collections import OrderedDict
from flask import jsonify, send_file, Response
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from data_prep_and_insert import refresh_database

from data_prep_and_insert import process_file, file_processing
from utils.sqls import get_latest_search, get_prices_over_time, get_entire_search, get_price_change
from db import db

blp = Blueprint("detailed", __name__, description="Utilities and queries concering just the data for selected city and size of apartment")

@blp.route("/latest/csv/<city>/<min_s>/<max_s>")
class LatestSearchCsv(MethodView):
    def get(self, city, min_s, max_s):
        try:
            df = pd.read_sql(get_latest_search(city, min_s, max_s), db.engine)
            csv_data = df.to_csv(index_label='index')
            # Create a Flask Response object with the CSV data
            response = Response(csv_data, content_type='text/csv')
            # Set the Content-Disposition header to prompt download the file
            response.headers['Content-Disposition'] = f'attachment; filename={city}_latest.csv'
            return response, 200
        except Exception as e:
            error_traceback = traceback.format_exc()
            error_message = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'error_traceback': error_traceback
            }
            return jsonify(error_message), 404

@blp.route("/latest/json/<city>/<min_s>/<max_s>")
class LatestSearch(MethodView):
    def get(self, city, min_s, max_s):
        temp_dir = tempfile.mkdtemp()  # Create a file in temp directory
        try:
            df = pd.read_sql(get_latest_search(city, min_s, max_s), db.engine)
            json_data = df.to_dict(orient="index", into=OrderedDict)
            json_file_path = os.path.join(temp_dir, f"{city}_all.json")
            with open(json_file_path, "w") as json_file:
                json.dump(json_data, json_file)
            return send_file(json_file_path, as_attachment=True), 200
        except Exception as e:
            error_traceback = traceback.format_exc()
            error_message = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'error_traceback': error_traceback
            }
            return jsonify(error_message), 404
        finally:
            # Clean up temporary directory after sending the file
            shutil.rmtree(temp_dir, ignore_errors=True)


@blp.route("/all/csv/<city>/<min_s>/<max_s>")
class EntireSearchCsv(MethodView):
    def get(self, city, min_s, max_s):
        try:
            df = pd.read_sql(get_entire_search(city, min_s, max_s), db.engine)
            csv_data = df.to_csv(index_label='index')
            # Create a Flask Response object with the CSV data
            response = Response(csv_data, content_type='text/csv')
            # Set the Content-Disposition header to prompt download the file
            response.headers['Content-Disposition'] = f'attachment; filename={city}_all.csv'
            return response, 200
        except Exception as e:
            error_traceback = traceback.format_exc()
            error_message = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'error_traceback': error_traceback
            }
            return jsonify(error_message), 404


@blp.route("/all/json/<city>/<min_s>/<max_s>")
class EntireSearch(MethodView):
    def get(self, city, min_s, max_s):
        temp_dir = tempfile.mkdtemp()
        try:
            df = pd.read_sql(get_entire_search(city, min_s, max_s), db.engine)
            for col in df.columns:
                df[col] = df[col].astype(str)
            json_data = df.to_dict(orient="index", into=OrderedDict)

            #temp_dir = tempfile.mkdtemp()
            json_file_path = os.path.join(temp_dir, f"{city}_all.json")
            with open(json_file_path, "w") as json_file:
                json.dump(json_data, json_file)
            #return jsonify(json_data), 200
            return send_file(json_file_path, as_attachment=True), 200
        except Exception as e:
            error_traceback = traceback.format_exc()
            error_message = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'error_traceback': error_traceback
            }
            return jsonify(error_message), 404
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


@blp.route("/prices_over_time/json/<city>/<min_s>/<max_s>")
class PricesOverTime(MethodView):
    def get(self, city, min_s, max_s):
        temp_dir = tempfile.mkdtemp()  # Create a file in temp directory
        try:
            df = pd.read_sql(get_prices_over_time(city, min_s, max_s), db.engine)
            df["scrapped_time"] = df['scrapped_time'].astype(str)
            df.set_index("scrapped_time", inplace=True)
            json_data = df.to_dict(orient="index")
            json_data = {key: value["average_price_sqm"] for key, value in json_data.items()}
            json_file_path = os.path.join(temp_dir, f"{city}_all.json")
            with open(json_file_path, "w") as json_file:
                json.dump(json_data, json_file)
            return send_file(json_file_path, as_attachment=True), 200
        except Exception as e:
            error_traceback = traceback.format_exc()
            error_message = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'error_traceback': error_traceback
            }
            return jsonify(error_message), 404
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


@blp.route("/prices_over_time/csv/<city>/<min_s>/<max_s>")
class PricesOverTimeCsv(MethodView):
    def get(self, city, min_s, max_s):
        try:
            df = pd.read_sql(get_prices_over_time(city, min_s, max_s), db.engine)
            df["scrapped_time"] = df['scrapped_time'].astype(str)
            csv_data = df.to_csv(index_label='index')
            response = Response(csv_data, content_type='text/csv')
            response.headers['Content-Disposition'] = f'attachment; filename={city}_prices_over_time.csv'
            return response, 200
        except Exception as e:
            error_traceback = traceback.format_exc()
            error_message = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'error_traceback': error_traceback
            }
            return jsonify(error_message), 404


@blp.route("/price_change/json/<city>/<min_s>/<max_s>")
class PriceChange(MethodView):
    def get(self, city, min_s, max_s):
        temp_dir = tempfile.mkdtemp()
        try:
            df = pd.read_sql(get_price_change(city, min_s, max_s), db.engine)
            df["time_price"] = df.apply(lambda row: {str(row["scrap_time"]): row["price"]}, axis=1)
            grouped_df = df.groupby('link')['time_price'].agg(list).reset_index()
            grouped_df.set_index("link", inplace=True)
            json_data = grouped_df.to_dict(orient='index')
            json_file_path = os.path.join(temp_dir, f"{city}_price_change.json")
            with open(json_file_path, "w") as json_file:
                json.dump(json_data, json_file)
            return send_file(json_file_path, as_attachment=True), 200
        except Exception as e:
            error_message = {'error_type': type(e).__name__, 'error_message': str(e)}
            return jsonify(error_message), 404
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

@blp.route("/price_change/csv/<city>/<min_s>/<max_s>")
class PriceChange(MethodView):
    def get(self, city, min_s, max_s):
        try:
            df = pd.read_sql(get_price_change(city, min_s, max_s), db.engine)
            df["time_price"] = df.apply(lambda row: {str(row["scrap_time"]): row["price"]}, axis=1)
            grouped_df = df.groupby('link')['time_price'].agg(list).reset_index()
            grouped_df.set_index("link", inplace=True)
            csv_data = grouped_df.to_csv(index_label='index')
            response = Response(csv_data, content_type='text/csv')
            response.headers['Content-Disposition'] = f'attachment; filename={city}_price_change.csv'
            return response, 200

        except Exception as e:
            error_message = {'error_type': type(e).__name__, 'error_message': str(e)}
            return jsonify(error_message), 404




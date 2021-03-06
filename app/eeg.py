from flask import Flask
from flask_cors import CORS
import pandas as pd
from sklearn.externals import joblib
from sklearn import pipeline
from sklearn.ensemble import RandomForestClassifier
import argparse
import numpy as np
import brainflow
from brainflow.board_shim import BoardShim, BrainFlowInputParams
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations
#import os


def make_app():

    app = Flask(__name__)
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    @app.route('/')
    def return_prediction():

        #ms = post_id
        # Lines 27-65 copied from https://brainflow.readthedocs.io/en/stable/Examples.html
        # use docs to check which parameters are required for specific board, e.g. for Cyton - set serial port

        parser = argparse.ArgumentParser()
        parser.add_argument('--ip-port', type = int, help  = 'ip port', required = False, default = 0)
        parser.add_argument('--ip-protocol', type = int, help  = 'ip protocol, check IpProtocolType enum', required = False, default = 0)
        parser.add_argument('--ip-address', type = str, help  = 'ip address', required = False, default = '')
        parser.add_argument('--serial-port', type = str, help  = 'serial port', required = False, default = '')
        parser.add_argument('--mac-address', type = str, help  = 'mac address', required = False, default = '')
        parser.add_argument('--other-info', type = str, help  = 'other info', required = False, default = '')
        parser.add_argument('--streamer-params', type = str, help  = 'other info', required = False, default = '')
        parser.add_argument('--board-id', type = int, help  = 'board id, check docs to get a list of supported boards', required = True)
        parser.add_argument('--log', action = 'store_true')
        args = parser.parse_args()

        params = BrainFlowInputParams()
        params.ip_port = args.ip_port
        params.serial_port = args.serial_port
        params.mac_address = args.mac_address
        params.other_info = args.other_info
        params.ip_address = args.ip_address
        params.ip_protocol = args.ip_protocol

        if (args.log):
            BoardShim.enable_dev_board_logger()
        else:
            BoardShim.disable_board_logger()

        board = BoardShim(args.board_id, params)
        board.prepare_session()

        board.start_stream () # use this for default options
        board.start_stream (ms, args.streamer_params)
        time.sleep(3000/1000)
        data = board.get_current_board_data (256) # get latest 256 packages or less, doesnt remove them from internal buffer
        data = board.get_board_data() # get all data and remove it from internal buffer
        board.stop_stream()
        board.release_session()


        # CONNECT THE DATA TO THE MODEL FOR PREDICTIONS

        # Test Sample Data
        #data = 'https://archlife.org/wp-content/uploads/2020/03/OpenBCI-RAW-right0.txt'

        column_names = ['index', 'channel1','channel2', 'channel3', 'channel4', 'accel1', 'accel2', 'accel3', 'timestamp', 'aux']
        dropped_row_indices = [0, 1, 2, 3, 4, 5]

        df = pd.read_csv(data, sep=',', header=None, names=column_names)
        df = df.drop(dropped_row_indices, axis=0).reset_index()
        df = df.drop(['level_0', 'index', 'timestamp'], axis=1)
        df = df.dropna(axis=0)

        model = joblib.load('flask_test/rfc.joblib')

        commands_proba = model.predict_proba(df)
        commands_pred = model.predict(df)

        commands_df = pd.DataFrame({'index': df.index, 'predictions':commands_pred})
        commands_df['predictions'] = commands_df['predictions'].astype('int64')
        command_count = commands_df['predictions'].value_counts()
        ccdf = pd.DataFrame({'index': command_count.index, 'predictions':command_count})
        preds = ccdf['index'].values
        command_pred = preds[0]

        return str(command_pred)

    return app

        #return "server response 200"

    #@app.route('/command/')
    #def predict():
        #ms = post_id




# r = requests.get(url = URL, params = PARAMS)

#export FLASK_APP=app:make_app
#flask run

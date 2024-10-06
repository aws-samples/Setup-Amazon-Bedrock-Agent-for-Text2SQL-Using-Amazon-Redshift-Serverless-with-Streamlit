#!/bin/bash

# Find and kill the existing Streamlit process
pid=$(ps aux | grep '[s]treamlit run app.py' | awk '{print $2}')
if [ ! -z "$pid" ]; then
    echo "Killing existing Streamlit process with PID: $pid"
    kill $pid
    sleep 2
    # Force kill if it's still running
    if ps -p $pid > /dev/null; then
        echo "Force killing the process"
        kill -9 $pid
    fi
fi

# Restart the Streamlit app
echo "Restarting Streamlit app"
cd /home/ubuntu/app/streamlit_app
nohup streamlit run app.py --server.port=8501 --server.address=0.0.0.0 > /home/ubuntu/app/streamlit_app/streamlit.log 2>&1 &

echo "Streamlit app restarted"
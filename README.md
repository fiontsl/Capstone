# Capstone Project - 5 Sec Recipe Search

This website allows you to find delicious cooking ideas by searching for ingredients you have in your kitchen, while also providing a range of useful features to make cooking easy and affordable. 

Enter any ingredient you have available and it instantly provides a range of recipes that use as many of your available ingredients as possible, while limiting the number of missing ingredients, time and cost. You can also filter options such as dish types and diet types.

![website_screenshots_1](https://github.com/fiontsl/Capstone/assets/33294622/2082db7c-7c7f-4346-903f-3fc984296e40)


Here’s how it works: 

![TDI Capstone Website](https://github.com/fiontsl/Capstone/assets/33294622/b2ab8776-a0fc-4357-a725-01f313c9f969)

How to reproduce the website:

1) If you are hosting this website on a cloud service, you will need to first create an account and run Ngrok:
    from pyngrok import ngrok 
    !ngrok config add-authtoken (your_token)

2) Install requirements.txt
    !pip install -r requirements.txt

3) You should also have a seperate config.json file to contain the keys. They should look like this:
   
   {
    "aws_access_key_id": "your_aws_access_key_id",
    "aws_secret_access_key": "your_aws_secret_access_key",
    "apiKey_spoonacular": "your_apiKey_spoonacular"
    }

4) Run streamlit_app.py 

5) To get a Ngrok Tunnel link to the website, run the following:

    import os
    !nohup streamlit run /content/streamlit_app.py --server.port 8501 &
    import time
    time.sleep(5) # Wait for Streamlit to start running
    from pyngrok import ngrok
    url = ngrok.connect(proto='http', addr='8501')
    print(url)

6) You should get an output that look like this:

    nohup: appending output to 'nohup.out'
    WARNING:pyngrok.process.ngrok:t=2023-06-02T22:43:51+0000 lvl=warn msg="ngrok config file found at legacy location, move to XDG location" xdg_path=/root/.config/ngrok/ngrok.yml legacy_path=/root/.ngrok2/ngrok.yml
    NgrokTunnel: "https://071d-34-86-164-136.ngrok-free.app" -> "http://localhost:8501"

7) To check you tunnels:
    tunnels = ngrok.get_tunnels()

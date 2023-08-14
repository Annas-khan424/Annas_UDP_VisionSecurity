import requests

# Replace this with the URL of your Flask app
url = 'http://127.0.0.1:5000/process_photo'

# Replace this with the path to the image file you want to test
image_file_path = 'C:\\Users\\Khan Machine\\Pictures\\check.jpg'




# Send the POST request with the image file
with open(image_file_path, 'rb') as file:
    files = {'file': file}
    response = requests.post(url, files=files)

# Print the response
if response.status_code == 200:
    data = response.json()
    if 'qr_code_data' in data:
        print("QR Code Data:")
        for qr_data in data['qr_code_data']:
            print(qr_data)
    elif 'result' in data:
        print(data['result'])
    elif 'error' in data:
        print("Error:", data['error'])
else:
    print("Error occurred. Status code:", response.status_code)

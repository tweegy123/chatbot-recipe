RECIPE FINDER CHATBOT (XAMPP + Python)

1. Install Python from python.org (tick "Add python.exe to PATH").
2. Copy this whole folder to C:\xampp\htdocs\  (so you have C:\xampp\htdocs\recipe-chatbot).
3. Open XAMPP Control Panel and start Apache.
4. Test the backend: open http://localhost/recipe-chatbot/chat.py
   You should see text starting with {"reply": "Hi! ...
5. Open the chatbot: http://localhost/recipe-chatbot/

If step 4 shows "Internal Server Error":
 - Open chat.py and change the first line from  #!python
   to your full Python path, for example  #!C:/Users/YourName/AppData/Local/Programs/Python/Python312/python.exe
   (run  where python  in Command Prompt to find it).
 - Check C:\xampp\apache\logs\error.log for details.

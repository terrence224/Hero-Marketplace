The online sub-domain for Hero-Marketplace is https://herajian.pythonanywhere.com

Installation Instructions

1. Download the codes through zip file or git clone https://github.com/terrence224/Hero-Marketplace.git
2. Go to the folder where app.py, requirements.txt and README.md are located
3. Create a new text file named ".env" within the same location (remove the "" and it should just be .env)
4. Open the .env and paste these keys (remove any indentation if necessarry)
   # Flask Configuration
   FLASK_SECRET_KEY="your_secure_random_secret_key_here"

   # Google OAuth Configuration
   GOOGLE_CLIENT_ID="820568194855-ndd9hnpga638na4uekpngtg0bagv0jpt.apps.googleusercontent.com"
   GOOGLE_CLIENT_SECRET="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"

   # Supabase Configuration
   SUPABASE_URL="https://tgoohuujseoaeyuprxfn.supabase.co"
   SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRnb29odXVqc2VvYWV5dXByeGZuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI4ODA0MjYsImV4cCI6MjA1ODQ1NjQyNn0.JFE3mupXYRVivpV0sWP0XR-aUHLb4cjNVCuYfNPT0_I"
5. Open a command line and install all the dependencies located at requirements.txt, through pip install -r requirements.txt, or manually pip install everything
6. Run app.py through a command line within the directory or through a Python IDE
7. Paste the local link to a browser, it should show as http://127.0.0.1:5000/

CONGRATS!!
You are now running Hero-Marketplace locally

The online sub-domain for Hero-Marketplace is https://herajian.pythonanywhere.com/

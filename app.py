import os
from flask import Flask, redirect, request, url_for, session, render_template, flash
from authlib.integrations.flask_client import OAuth
from functools import wraps
from dotenv import load_dotenv
from datetime import timedelta
from supabase import create_client, Client

# Load environment variables
load_dotenv()


# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
app.permanent_session_lifetime = timedelta(days=5)

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)


# Setup OAuth
oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    access_token_url="https://accounts.google.com/o/oauth2/token",
    access_token_params=None,
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    authorize_params=None,
    api_base_url="https://www.googleapis.com/oauth2/v1/",
    client_kwargs={"scope": "openid email profile"},
)

# Admin whitelist (list of email addresses that have admin privileges)
ADMIN_EMAILS = [
    "gionterrence.pozon@my.jru.edu",
    # Add more admin emails as needed
]

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    # Redirect all logged-in users to the home view
    if 'user' in session:
        return redirect(url_for('view_listings'))
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login/google')
def login_with_google():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    try:
        token = google.authorize_access_token()
        resp = google.get('userinfo')
        user_info = resp.json()
        
        # Store user info in session
        session['user'] = user_info
        session.permanent = True
        
        # Check if user exists and determine user type
        email = user_info.get('email')
        # Simplify: set type, then single redirect
        session['user_type'] = 'admin' if email in ADMIN_EMAILS or email.endswith('@jru.edu') else 'user'
        return redirect(url_for('view_listings'))
            
    except Exception as e:
        print(f"Error during authorization: {e}")
        return redirect(url_for('login', error='Authentication failed'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('user_type', None)
    return redirect(url_for('login'))


@app.route('/listings')
@login_required
def view_listings():
    try:
        category = request.args.get('category', None)
        
        # Query Supabase for listings
        query = supabase.table('listings').select('*')
        
        # Filter by category if provided
        if category:
            query = query.eq('category', category)
            
        response = query.execute()
        listings = response.data
        
        return render_template('home.html', listings=listings, user=session.get('user', {}))
    except Exception as e:
        print(f"Error fetching listings: {e}")
        return render_template('home.html', listings=[], error="Failed to load listings", user=session.get('user', {}))

@app.route('/listings/create', methods=['GET', 'POST'])
@login_required
def create_listing():
    if request.method == 'GET':
        return render_template('home.html', user=session.get('user', {}))
    
    if request.method == 'POST':
        try:
            # Get current user's email from session
            user_email = session.get('user', {}).get('email')
            
            if not user_email:
                flash("You must be logged in to create a listing")
                return redirect(url_for('view_listings'))
            
            # Extract form data
            title = request.form.get('title')
            description = request.form.get('description')
            price = request.form.get('price')
            status = request.form.get('status', 'Available')
            contact = request.form.get('contact')
            category = request.form.get('category')
            
            # Validate required fields
            if not all([title, description, price, contact, category]):
                flash("All fields are required")
                return redirect(url_for('view_listings'))
            
            # Insert into Supabase
            listing_data = {
                'title': title,
                'description': description,
                'price': float(price),
                'status': status,
                'contact': contact,
                'category': category,
                'gmail': user_email
            }
            
            response = supabase.table('listings').insert(listing_data).execute()
            
            if response.data:
                flash("Listing created successfully!")
            else:
                flash("Failed to create listing")
                
            return redirect(url_for('view_listings'))
                
        except Exception as e:
            print(f"Error creating listing: {e}")
            flash("An error occurred while creating your listing")
            return redirect(url_for('view_listings'))

@app.route('/listings/<int:listing_id>')
def view_listing(listing_id):
    try:
        response = supabase.table('listings').select('*').eq('id', listing_id).execute()
        
        if response.data and len(response.data) > 0:
            listing = response.data[0]
            return render_template('home.html', listing_detail=listing, user=session.get('user', {}))
        else:
            flash("Listing not found")
            return redirect(url_for('view_listings'))
    except Exception as e:
        print(f"Error fetching listing: {e}")
        flash("Failed to load listing details")
        return redirect(url_for('view_listings'))

@app.route('/listings/<int:listing_id>/edit', methods=['POST'])
@login_required
def edit_listing(listing_id):
    # Get current user's email
    user_email = session.get('user', {}).get('email')
    
    if not user_email:
        flash("You must be logged in to edit a listing")
        return redirect(url_for('view_listings'))
    
    try:
        # Get the listing
        response = supabase.table('listings').select('*').eq('id', listing_id).execute()
        
        if not response.data or len(response.data) == 0:
            flash("Listing not found")
            return redirect(url_for('view_listings'))
            
        listing = response.data[0]
        
        # Check if user owns this listing or is an admin
        if listing['gmail'] != user_email and session.get('user_type') != 'admin':
            flash("You don't have permission to edit this listing")
            return redirect(url_for('view_listings'))
        
        # Extract form data
        title = request.form.get('title')
        description = request.form.get('description')
        price = request.form.get('price')
        status = request.form.get('status')
        contact = request.form.get('contact')
        category = request.form.get('category')
        
        # Validate required fields
        if not all([title, description, price, contact, category, status]):
            flash("All fields are required")
            return redirect(url_for('view_listings'))
        
        # Update in Supabase
        listing_data = {
            'title': title,
            'description': description,
            'price': float(price),
            'status': status,
            'contact': contact,
            'category': category
        }
        
        update_response = supabase.table('listings').update(listing_data).eq('id', listing_id).execute()
        
        if update_response.data:
            flash("Listing updated successfully!")
        else:
            flash("Failed to update listing")
            
        return redirect(url_for('view_listings'))
                
    except Exception as e:
        print(f"Error updating listing: {e}")
        flash("An error occurred while updating your listing")
        return redirect(url_for('view_listings'))

@app.route('/listings/<int:listing_id>/delete', methods=['POST'])
@login_required
def delete_listing(listing_id):
    # Get current user's email
    user_email = session.get('user', {}).get('email')
    
    if not user_email:
        flash("You must be logged in to delete a listing")
        return redirect(url_for('view_listings'))
    
    try:
        # Get the listing
        response = supabase.table('listings').select('*').eq('id', listing_id).execute()
        
        if not response.data or len(response.data) == 0:
            flash("Listing not found")
            return redirect(url_for('view_listings'))
            
        listing = response.data[0]
        
        # Check if user owns this listing or is an admin
        if listing['gmail'] != user_email and session.get('user_type') != 'admin':
            flash("You don't have permission to delete this listing")
            return redirect(url_for('view_listings'))
        
        # Delete from Supabase
        delete_response = supabase.table('listings').delete().eq('id', listing_id).execute()
        
        if delete_response.data:
            flash("Listing deleted successfully!")
        else:
            flash("Failed to delete listing")
            
        return redirect(url_for('view_listings'))
                
    except Exception as e:
        print(f"Error deleting listing: {e}")
        flash("An error occurred while deleting your listing")
        return redirect(url_for('view_listings'))

@app.route('/my-listings')
@login_required
def my_listings():
    try:
        # Get current user's email
        user_email = session.get('user', {}).get('email')
        
        if not user_email:
            flash("You must be logged in to view your listings")
            return redirect(url_for('view_listings'))
        
        # Query Supabase for user's listings
        response = supabase.table('listings').select('*').eq('gmail', user_email).execute()
        listings = response.data
        
        return render_template('home.html', listings=listings, user=session.get('user', {}), view_type='my_listings')
    except Exception as e:
        print(f"Error fetching user listings: {e}")
        return render_template('home.html', listings=[], error="Failed to load your listings", user=session.get('user', {}))


if __name__ == "__main__":
    app.run(debug=True)
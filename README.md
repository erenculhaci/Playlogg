# Playlogg 🎮 [https://playlogg.onrender.com](https://playlogg.onrender.com)

[![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/CSS)
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![AWS S3](https://img.shields.io/badge/AWS_S3-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)](https://aws.amazon.com/s3/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com/)

Playlogg is a comprehensive game discovery and logging platform - think IMDb or Letterboxd but for video games! Track your gaming journey, rate games, share opinions, and discover new titles all in one place.

![playlogg](https://github.com/user-attachments/assets/e0dc4d46-4ebb-4322-9cb1-b0d906fd7e5f)


## 🌟 Features

- **User Authentication System**
  - Secure registration with email verification
  - Password reset functionality
  - Profile management with AWS S3 image storage

- **Game Discovery**
  - Advanced filtering by genre, platform, studio, and release year
  - Rating-based filtering for finding the best games
  - Smart sorting options (recent, popular, alphabetical)
  - Efficient search functionality

- **Game Database**
  - Detailed game information including title, description, release date, studio
  - Genre and platform tags
  - Game cover images stored on AWS S3

- **Game Interaction**
  - Personal game logs with multiple status options (Played, Completed, Abandoned, etc.)
  - Rating system with decimal precision and average ratings
  - Game time tracking
  - Notes and comments on games

- **Social Features**
  - Comment system with nested replies
  - Like functionality for games and comments
  - View other users' profiles and game collections, likes or logs

- **Performance Optimized**
  - Database query optimization
  - Caching strategy for frequently accessed data
  - Efficient pagination

## 🛠️ Technology Stack

### Backend
- **[Django](https://www.djangoproject.com/)** - Web framework
- **[PostgreSQL](https://www.postgresql.org/)** - Database with JSON field support
- **[Django ORM](https://docs.djangoproject.com/en/4.2/topics/db/queries/)** - Database query optimization
- **AWS S3** - Media storage solution
- **Custom signals** - For handling media cleanup and updates

### Frontend
- **Django Templates** - Server-side rendering
- **[Tailwind CSS](https://tailwindcss.com/)** - Utility-first CSS framework
- **[SweetAlert2](https://sweetalert2.github.io/)** - Beautiful, responsive popups
- **JavaScript** - For interactive elements

### Authentication & Security
- **Django Auth** - User authentication system
- **Email verification** - For secure account creation
- **Password hashing** - For secure password storage

### DevOps
- **[Render](https://render.com/)** - Cloud hosting and deployment
- **Environment Variables** - Secure configuration management
- **AWS S3 Integration** - For media file storage

### Communication
- **Gmail SMTP** - Email service integration
- **HTML Email Templates** - Professional communication

### Performance Optimization
- **Database indexing** - For faster queries
- **Query optimization** - Minimizing database hits
- **Caching** - For frequently accessed data
- **Pagination** - For handling large datasets efficiently

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- PostgreSQL
- AWS S3 bucket
- Email service account

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/erenculhaci/Playlogg.git
   cd Playlogg
   ```

2. Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables
   ```bash
   # Create a .env file with the following variables
   SECRET_KEY=your_secret_key
   DEBUG=True
   DATABASE_URL=postgres://user:password@localhost/playlogg
   
   # AWS S3 configuration
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   AWS_STORAGE_BUCKET_NAME=your_bucket_name
   AWS_S3_REGION_NAME=your_region
   
   # Email configuration
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=465
   EMAIL_HOST_USER=your_email@gmail.com
   EMAIL_HOST_PASSWORD=your_app_password
   EMAIL_USE_TLS=False
   EMAIL_USE_SSL=True
   ```

5. Apply migrations
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. Run the development server
   ```bash
   python manage.py runserver
   ```

7. Visit `http://127.0.0.1:8000` in your browser

## 🌐 Deployment

The application is deployed on Render's cloud platform. The free tier may result in slower initial load times due to container spin-up.

## 💾 Database Design

Playlogg uses a PostgreSQL database with optimized models:

- **User & Profile**: Extended Django User model with additional profile information
- **Game**: Comprehensive game data with JSONField for flexible genre and platform storage
- **GameLog**: User-game relationships with status, ratings, and play time
- **Comment**: Hierarchical comment system with reply functionality

Database optimization techniques:
- Strategic indexing for frequently queried fields
- JSON field indexing using GIN for faster searches
- Query optimization with select_related and prefetch_related
- Efficient pagination to handle large datasets

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🧑‍💻 Author

Created by [Eren Culhacı](https://github.com/erenculhaci)

---

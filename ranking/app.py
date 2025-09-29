import os
from flask import Blueprint, render_template, request, jsonify, session
from sqlalchemy import func, desc, case
from extensions import db
from models import User, Transaction, Review, Product
from datetime import datetime, timedelta
import logging
from decorators import restrict_banned

ranking_bp = Blueprint('ranking', __name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

logger = logging.getLogger(__name__)

@ranking_bp.route('/')
@restrict_banned
def index():
    try:
        # Get transaction volume ranking
        transaction_rankings = get_transaction_rankings()

        # Get review rating ranking
        review_rankings = get_review_rankings()

        return render_template('ranking_index.html', transaction_rankings=transaction_rankings, review_rankings=review_rankings)
    
    except Exception as e:
        logger.error(f"Error in ranking index: {str(e)}")
        return render_template('ranking_index.html', transaction_rankings=[], review_rankings=[])


def get_transaction_rankings():
    try:
        # Count transactions of buyer
        buyer_counts = db.session.query(
            Transaction.buyer_id.label('user_id'), 
            func.count(Transaction.id).label('buyer_count')
        ).group_by(Transaction.buyer_id).subquery()

        # Count transactions of seller
        seller_counts = db.session.query(
            Transaction.seller_id.label('user_id'), 
            func.count(Transaction.id).label('seller_count')
        ).group_by(Transaction.seller_id).subquery()

        # Combine buyer and seller count
        rankings_query = db.session.query(
            User.id,
            User.name,
            User.profile_pic,
            User.join_date,
            func.coalesce(buyer_counts.c.buyer_count, 0).label('buyer_transactions'),
            func.coalesce(seller_counts.c.seller_count, 0).label('seller_transactions'),
            (func.coalesce(buyer_counts.c.buyer_count, 0) + 
             func.coalesce(seller_counts.c.seller_count, 0)).label('total_transactions')
            ).outerjoin(
                buyer_counts, User.id == buyer_counts.c.user_id
            ).outerjoin(
                seller_counts, User.id == seller_counts.c.user_id
            ).filter(
                (func.coalesce(buyer_counts.c.buyer_count, 0) +
                 func.coalesce(seller_counts.c.seller_count, 0)) > 0
            ).order_by(desc('total_transactions')).limit(50)
        
        rankings = []
        for rank, user_data in enumerate(rankings_query.all(), 1):
            rankings.append({
                'rank': rank,
                'user_id': user_data.id,
                'name': user_data.name,
                'profile_pic': user_data.profile_pic,
                'join_date': user_data.join_date,
                'buyer_transactions': user_data.buyer_transactions,
                'seller_transactions': user_data.seller_transactions,
                'total_transactions': user_data.total_transactions,
                })
            
        return rankings


    except Exception as e:
        logger.error(f"Error calculating transaction volume: {str(e)}")
        return []


def get_review_rankings():
    try:
        # Query to get review statistics for each user
        review_stats = db.session.query(
            Review.seller_id.label('user_id'),
            func.count(Review.id).label('total_reviews'),
            func.avg(Review.rating).label('average_rating'),
            func.sum(case((Review.rating >= 4, 1), else_=0)).label('positive_reviews')
        ).group_by(Review.seller_id).subquery()

        # Get user details with review statistics
        rankings_query = db.session.query(
            User.id,
            User.name,
            User.profile_pic,
            User.join_date,
            review_stats.c.total_reviews,
            review_stats.c.average_rating,
            review_stats.c.positive_reviews,
            (review_stats.c.positive_reviews * 100.0 / review_stats.c.total_reviews).label('positive_percentage')
            ).join(
                review_stats, User.id == review_stats.c.user_id
            ).order_by(desc('average_rating')).limit(50)
        
        rankings = []
        for rank, user_data in enumerate(rankings_query.all(), 1):
            rankings.append({
                'rank': rank,
                'user_id': user_data.id,
                'name': user_data.name,
                'profile_pic': user_data.profile_pic,
                'join_date': user_data.join_date,
                'total_reviews': user_data.total_reviews,
                'average_rating': round(user_data.average_rating, 2),
                'positive_reviews': user_data.positive_reviews,
                'positive_percentage': round(user_data.positive_percentage, 1)
                })
            
        return rankings


    except Exception as e:
        logger.error(f"Error calculating transaction volume: {str(e)}")
        return []
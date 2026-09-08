from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.product_view import ProductView
from app.models.review import Review


def get_recommendations(
    db: Session,
    user_id: int,
    limit: int = 10
):
    """
    Generate personalized product recommendations
    based on:

    1. User browsing history
    2. Past purchases
    3. Product category similarity
    4. Most viewed products
    5. Top-rated products
    """

    scores = defaultdict(float)

    # -------------------------------------------------
    # 1. GET USER'S VIEWING HISTORY
    # -------------------------------------------------

    viewed_products = (
        db.query(
            ProductView.product_id,
            func.count(ProductView.id).label("view_count")
        )
        .filter(
            ProductView.user_id == user_id
        )
        .group_by(
            ProductView.product_id
        )
        .order_by(
            func.count(ProductView.id).desc()
        )
        .all()
    )

    viewed_product_ids = {
        product_id
        for product_id, _ in viewed_products
    }

    # -------------------------------------------------
    # 2. GET USER'S PAST PURCHASES
    # -------------------------------------------------

    purchased_products = (
        db.query(
            OrderItem.product_id,
            func.sum(OrderItem.quantity).label("quantity")
        )
        .join(
            Order,
            OrderItem.order_id == Order.id
        )
        .filter(
            Order.user_id == user_id,
            Order.status != "cancelled"
        )
        .group_by(
            OrderItem.product_id
        )
        .all()
    )

    purchased_product_ids = {
        product_id
        for product_id, _ in purchased_products
    }

    # -------------------------------------------------
    # 3. ADD SCORE FOR USER'S VIEWING HISTORY
    # -------------------------------------------------

    for product_id, view_count in viewed_products:

        # More views = stronger interest
        scores[product_id] += min(view_count * 3, 15)

    # -------------------------------------------------
    # 4. ADD SCORE FOR PAST PURCHASES
    # -------------------------------------------------

    for product_id, quantity in purchased_products:

        scores[product_id] += min(quantity * 5, 20)

    # -------------------------------------------------
    # 5. FIND USER'S PREFERRED CATEGORIES
    # -------------------------------------------------

    interested_product_ids = (
        viewed_product_ids |
        purchased_product_ids
    )

    interested_categories = set()

    if interested_product_ids:

        categories = (
            db.query(Product.category)
            .filter(
                Product.id.in_(interested_product_ids)
            )
            .all()
        )

        interested_categories = {
            category
            for category, in categories
            if category
        }

    # -------------------------------------------------
    # 6. CATEGORY SIMILARITY
    # -------------------------------------------------

    if interested_categories:

        similar_products = (
            db.query(Product)
            .filter(
                Product.category.in_(interested_categories),
                Product.stock > 0
            )
            .all()
        )

        for product in similar_products:

            # Products from categories the user interacted
            # with receive a recommendation boost.
            scores[product.id] += 8

    # -------------------------------------------------
    # 7. MOST VIEWED / POPULAR PRODUCTS
    # -------------------------------------------------

    popular_products = (
        db.query(Product)
        .filter(
            Product.stock > 0
        )
        .order_by(
            Product.popularity.desc()
        )
        .limit(20)
        .all()
    )

    for product in popular_products:

        # Popularity contributes to recommendation score
        popularity_score = min(
            product.popularity / 10,
            10
        )

        scores[product.id] += popularity_score

    # -------------------------------------------------
    # 8. TOP-RATED PRODUCTS
    # -------------------------------------------------

    top_rated_products = (
        db.query(
            Product.id,
            func.avg(Review.rating).label("average_rating"),
            func.count(Review.id).label("review_count")
        )
        .join(
            Review,
            Review.product_id == Product.id
        )
        .filter(
            Review.status == "approved",
            Product.stock > 0
        )
        .group_by(
            Product.id
        )
        .having(
            func.count(Review.id) >= 1
        )
        .order_by(
            func.avg(Review.rating).desc()
        )
        .limit(20)
        .all()
    )

    for product_id, average_rating, review_count in top_rated_products:

        rating_score = float(average_rating or 0)

        # Highly rated products receive a boost
        scores[product_id] += rating_score * 2

    # -------------------------------------------------
    # 9. REMOVE PRODUCTS ALREADY PURCHASED
    # -------------------------------------------------

    for product_id in purchased_product_ids:

        scores.pop(product_id, None)

    # -------------------------------------------------
    # 10. GET FINAL PRODUCTS
    # -------------------------------------------------

    if not scores:
        return []

    ranked_product_ids = sorted(
        scores,
        key=scores.get,
        reverse=True
    )

    ranked_product_ids = ranked_product_ids[:limit]

    # -------------------------------------------------
    # 11. LOAD PRODUCTS
    # -------------------------------------------------

    products = (
        db.query(Product)
        .filter(
            Product.id.in_(ranked_product_ids),
            Product.stock > 0
        )
        .all()
    )

    # Preserve recommendation ranking
    product_map = {
        product.id: product
        for product in products
    }

    return [
        product_map[product_id]
        for product_id in ranked_product_ids
        if product_id in product_map
    ]
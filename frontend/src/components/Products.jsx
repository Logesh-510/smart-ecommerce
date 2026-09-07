import { useEffect, useState } from "react";
import api from "../api/api";
import { addToCart } from "../api/cart";

function Products() {
  const [products, setProducts] = useState([]);
  const [productReviews, setProductReviews] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [ratings, setRatings] = useState({});
  const [comments, setComments] = useState({});
  const [reviewMessages, setReviewMessages] = useState({});
  const [submittingReview, setSubmittingReview] = useState({});

  // =====================================================
  // Load Products
  // =====================================================

  useEffect(() => {
    loadProducts();
  }, []);

  async function loadProducts() {
    try {
      setLoading(true);

      const response = await api.get("/products/");

      setProducts(response.data);

      // Load reviews for every product
      const reviewsData = {};

      await Promise.all(
        response.data.map(async (product) => {
          try {
            const reviewResponse = await api.get(
              `/products/${product.id}/reviews`
            );

            reviewsData[product.id] = reviewResponse.data;
          } catch (error) {
            console.error(
              `Unable to load reviews for product ${product.id}`,
              error
            );
          }
        })
      );

      setProductReviews(reviewsData);
    } catch (error) {
      console.error(error);
      setError("Unable to load products");
    } finally {
      setLoading(false);
    }
  }

  // =====================================================
  // Load Reviews For One Product
  // =====================================================

  async function loadProductReviews(productId) {
    try {
      const response = await api.get(
        `/products/${productId}/reviews`
      );

      setProductReviews((previousReviews) => ({
        ...previousReviews,
        [productId]: response.data,
      }));
    } catch (error) {
      console.error("Unable to refresh reviews:", error);
    }
  }

  // =====================================================
  // Add To Cart
  // =====================================================

  async function handleAddToCart(productId) {
    try {
      await addToCart(productId, 1);

      alert("Product added to cart");
    } catch (error) {
      console.error("Add to cart error:", error);

      if (error.response) {
        alert(
          error.response.data?.detail ||
            "Unable to add product to cart"
        );
      } else {
        alert("Unable to connect to backend");
      }
    }
  }

  // =====================================================
  // Submit Review
  // =====================================================

  async function handleSubmitReview(productId) {
    const rating = ratings[productId];
    const comment = comments[productId] || "";

    // Validate rating
    if (!rating) {
      setReviewMessages((previous) => ({
        ...previous,
        [productId]: "Please select a rating.",
      }));

      return;
    }

    // Check login
    const token = localStorage.getItem("access_token");

    if (!token) {
      setReviewMessages((previous) => ({
        ...previous,
        [productId]: "Please login before submitting a review.",
      }));

      return;
    }

    try {
      setSubmittingReview((previous) => ({
        ...previous,
        [productId]: true,
      }));

      setReviewMessages((previous) => ({
        ...previous,
        [productId]: "",
      }));

      const response = await api.post("/reviews", {
        product_id: productId,
        rating: Number(rating),
        comment: comment.trim() || null,
      });

      console.log("Review created:", response.data);

      setReviewMessages((previous) => ({
        ...previous,
        [productId]:
          "Review submitted successfully! It is waiting for admin approval.",
      }));

      // Clear form
      setRatings((previous) => ({
        ...previous,
        [productId]: 0,
      }));

      setComments((previous) => ({
        ...previous,
        [productId]: "",
      }));

      // Refresh reviews
      await loadProductReviews(productId);
    } catch (error) {
      console.error("Review submission error:", error);

      let errorMessage = "Unable to submit review.";

      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (!error.response) {
        errorMessage = "Unable to connect to backend.";
      }

      setReviewMessages((previous) => ({
        ...previous,
        [productId]: errorMessage,
      }));
    } finally {
      setSubmittingReview((previous) => ({
        ...previous,
        [productId]: false,
      }));
    }
  }

  // =====================================================
  // Star Display
  // =====================================================

  function renderStars(rating) {
    const roundedRating = Math.round(rating || 0);

    return "★★★★★"
      .split("")
      .map((star, index) =>
        index < roundedRating ? "★" : "☆"
      )
      .join("");
  }

  // =====================================================
  // Loading / Error
  // =====================================================

  if (loading) {
    return <p>Loading products...</p>;
  }

  if (error) {
    return <p>{error}</p>;
  }

  // =====================================================
  // UI
  // =====================================================

  return (
    <section>
      <h2>Products</h2>

      {products.length === 0 ? (
        <p>No products available.</p>
      ) : (
        products.map((product) => {
          const reviewData = productReviews[product.id];

          const averageRating =
            reviewData?.average_rating || 0;

          const totalReviews =
            reviewData?.total_reviews || 0;

          const selectedRating =
            ratings[product.id] || 0;

          return (
            <div key={product.id}>
              <h3>{product.name}</h3>

              <p>{product.description}</p>

              <p>
                Category: {product.category}
              </p>

              <p>
                Price: ₹
                {Number(product.price).toLocaleString(
                  "en-IN"
                )}
              </p>

              <p>
                Stock: {product.stock}
              </p>

              <p>
                Popularity: {product.popularity}
              </p>

              {/* ===================================== */}
              {/* Product Rating */}
              {/* ===================================== */}

              <h4>Rating</h4>

              <p>
                {renderStars(averageRating)}{" "}
                {Number(averageRating).toFixed(1)}
              </p>

              <p>
                {totalReviews}{" "}
                {totalReviews === 1
                  ? "Review"
                  : "Reviews"}
              </p>

              {/* ===================================== */}
              {/* Top Reviews */}
              {/* ===================================== */}

              {reviewData?.top_reviews?.length > 0 && (
                <>
                  <h4>Top Reviews</h4>

                  {reviewData.top_reviews.map(
                    (review) => (
                      <div key={review.id}>
                        <p>
                          {renderStars(review.rating)}
                        </p>

                        {review.comment && (
                          <p>{review.comment}</p>
                        )}

                        <p>
                          User #{review.user_id}
                        </p>
                      </div>
                    )
                  )}
                </>
              )}

              {/* ===================================== */}
              {/* All Reviews */}
              {/* ===================================== */}

              {reviewData?.reviews?.length > 0 && (
                <>
                  <h4>All Reviews</h4>

                  {reviewData.reviews.map((review) => (
                    <div key={review.id}>
                      <p>
                        {renderStars(review.rating)}
                      </p>

                      {review.comment && (
                        <p>{review.comment}</p>
                      )}

                      <p>
                        User #{review.user_id}
                      </p>

                      <p>
                        Status: {review.status}
                      </p>

                      <hr />
                    </div>
                  ))}
                </>
              )}

              {/* ===================================== */}
              {/* Write Review */}
              {/* ===================================== */}

              <h4>Write a Review</h4>

              <div>
                <p>Select Rating:</p>

                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() =>
                      setRatings((previous) => ({
                        ...previous,
                        [product.id]: star,
                      }))
                    }
                  >
                    {star <= selectedRating ? "★" : "☆"}
                  </button>
                ))}
              </div>

              <br />

              <div>
                <label
                  htmlFor={`comment-${product.id}`}
                >
                  Comment
                </label>

                <br />

                <textarea
                  id={`comment-${product.id}`}
                  value={comments[product.id] || ""}
                  onChange={(event) =>
                    setComments((previous) => ({
                      ...previous,
                      [product.id]: event.target.value,
                    }))
                  }
                  placeholder="Write your review..."
                  rows="4"
                  cols="40"
                />
              </div>

              <br />

              <button
                type="button"
                onClick={() =>
                  handleSubmitReview(product.id)
                }
                disabled={
                  submittingReview[product.id]
                }
              >
                {submittingReview[product.id]
                  ? "Submitting..."
                  : "Submit Review"}
              </button>

              {reviewMessages[product.id] && (
                <p>
                  {reviewMessages[product.id]}
                </p>
              )}

              <br />

              {/* ===================================== */}
              {/* Add To Cart */}
              {/* ===================================== */}

              <button
                onClick={() =>
                  handleAddToCart(product.id)
                }
              >
                Add to Cart
              </button>

              <hr />
            </div>
          );
        })
      )}
    </section>
  );
}

export default Products;
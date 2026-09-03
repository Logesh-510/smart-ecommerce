import { useEffect, useState } from "react";
import api from "../api/api";

function Orders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const [selectedOrder, setSelectedOrder] = useState(null);
  const [reason, setReason] = useState("");
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/orders");
      setOrders(response.data);
    } catch (error) {
      console.error(error);

      if (error.response?.status === 401) {
        setError("Please login to view your orders.");
      } else if (error.response?.data?.detail) {
        setError(error.response.data.detail);
      } else {
        setError("Failed to load orders.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, []);

  const isReturnWindowActive = (order) => {
    if (order.status !== "delivered" || !order.delivered_at) {
      return false;
    }

    const deliveredDate = new Date(order.delivered_at);
    const deadline = new Date(deliveredDate);
    deadline.setDate(deadline.getDate() + 7);

    return new Date() <= deadline;
  };

  const handleReturnClick = (order) => {
    setSelectedOrder(order);
    setReason("");
    setComment("");
    setMessage("");
    setError("");
  };

  const handleCancelReturn = () => {
    setSelectedOrder(null);
    setReason("");
    setComment("");
  };

  const handleReturnSubmit = async (event) => {
    event.preventDefault();

    if (!selectedOrder) {
      return;
    }

    if (!reason.trim()) {
      setError("Please select a return reason.");
      return;
    }

    try {
      setSubmitting(true);
      setMessage("");
      setError("");

      const response = await api.post(
        `/orders/${selectedOrder.id}/return`,
        {
          reason,
          comment: comment.trim() || null,
        }
      );

      setMessage(response.data.message);
      setSelectedOrder(null);
      setReason("");
      setComment("");

      await fetchOrders();
    } catch (error) {
      console.error(error);

      if (error.response?.data?.detail) {
        setError(error.response.data.detail);
      } else {
        setError("Failed to submit return request.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <section>
        <h2>My Orders</h2>
        <p>Loading orders...</p>
      </section>
    );
  }

  return (
    <section>
      <h2>My Orders</h2>

      {message && <p>{message}</p>}
      {error && <p>{error}</p>}

      {orders.length === 0 ? (
        <p>No orders found.</p>
      ) : (
        <div>
          {orders.map((order) => (
            <article key={order.id}>
              <hr />

              <h3>Order #{order.id}</h3>

              <p>
                <strong>Status:</strong>{" "}
                {order.status === "return_requested"
                  ? "Return Requested"
                  : order.status}
              </p>

              <p>
                <strong>Payment Status:</strong> {order.payment_status}
              </p>

              <p>
                <strong>Total:</strong> ₹{order.total_amount}
              </p>

              {order.delivered_at && (
                <p>
                  <strong>Delivered:</strong>{" "}
                  {new Date(order.delivered_at).toLocaleString()}
                </p>
              )}

              {order.status === "delivered" &&
                isReturnWindowActive(order) && (
                  <button
                    type="button"
                    onClick={() => handleReturnClick(order)}
                  >
                    Request Return
                  </button>
                )}

              {order.status === "return_requested" && (
                <p>
                  <strong>Return request:</strong> Pending
                </p>
              )}

              <h4>Items</h4>

              <ul>
                {order.items.map((item) => (
                  <li key={item.product_id}>
                    Product #{item.product_id} — Quantity:{" "}
                    {item.quantity} — ₹{item.price}
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      )}

      {selectedOrder && (
        <section>
          <hr />

          <h3>Request Return — Order #{selectedOrder.id}</h3>

          <form onSubmit={handleReturnSubmit}>
            <div>
              <label htmlFor="return-reason">
                Reason
              </label>

              <br />

              <select
                id="return-reason"
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                required
              >
                <option value="">Select a reason</option>
                <option value="Product damaged">
                  Product damaged
                </option>
                <option value="Wrong product received">
                  Wrong product received
                </option>
                <option value="Product defective">
                  Product defective
                </option>
                <option value="Product not as described">
                  Product not as described
                </option>
                <option value="Changed my mind">
                  Changed my mind
                </option>
                <option value="Other">Other</option>
              </select>
            </div>

            <br />

            <div>
              <label htmlFor="return-comment">
                Comment (optional)
              </label>

              <br />

              <textarea
                id="return-comment"
                value={comment}
                onChange={(event) => setComment(event.target.value)}
                placeholder="Add additional details about your return..."
                rows="4"
              />
            </div>

            <br />

            <button type="submit" disabled={submitting}>
              {submitting
                ? "Submitting..."
                : "Submit Return Request"}
            </button>

            {" "}

            <button
              type="button"
              onClick={handleCancelReturn}
              disabled={submitting}
            >
              Cancel
            </button>
          </form>
        </section>
      )}
    </section>
  );
}

export default Orders;
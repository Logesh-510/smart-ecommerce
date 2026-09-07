import { useEffect, useState } from "react";
import {
  getCart,
  updateCart,
  removeFromCart,
} from "../api/cart";
import { createOrder } from "../api/orders";

function Cart() {
  const [cart, setCart] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [placingOrder, setPlacingOrder] = useState(false);
  const [orderMessage, setOrderMessage] = useState("");

  async function loadCart() {
    try {
      setError("");

      const data = await getCart();

      setCart(data);
    } catch (error) {
      console.error("Cart error:", error);
      setError("Unable to load cart");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCart();
  }, []);

  async function handleUpdate(productId, quantity) {
    try {
      await updateCart(productId, quantity);
      await loadCart();
    } catch (error) {
      console.error("Update cart error:", error);
      alert("Unable to update cart");
    }
  }

  async function handleRemove(productId) {
    try {
      await removeFromCart(productId);
      await loadCart();
    } catch (error) {
      console.error("Remove cart error:", error);
      alert("Unable to remove product");
    }
  }

  async function handlePlaceOrder() {
    try {
      setPlacingOrder(true);
      setOrderMessage("");

      const order = await createOrder();

      setOrderMessage(
        `Order #${order.id} placed successfully!`
      );

      await loadCart();
    } catch (error) {
      console.error("Create order error:", error);

      if (error.response?.data?.detail) {
        setOrderMessage(error.response.data.detail);
      } else if (!error.response) {
        setOrderMessage(
          "Unable to connect to backend."
        );
      } else {
        setOrderMessage(
          "Unable to place order."
        );
      }
    } finally {
      setPlacingOrder(false);
    }
  }

  if (loading) {
    return <p>Loading cart...</p>;
  }

  if (error) {
    return <p>{error}</p>;
  }

  return (
    <section>
      <h2>Shopping Cart</h2>

      {cart.length === 0 ? (
        <p>Your cart is empty.</p>
      ) : (
        <>
          {cart.map((item) => (
            <div key={item.id}>
              <p>
                <strong>Product ID:</strong>{" "}
                {item.product_id}
              </p>

              <p>
                <strong>Quantity:</strong>{" "}
                {item.quantity}
              </p>

              <button
                onClick={() =>
                  handleUpdate(
                    item.product_id,
                    item.quantity + 1
                  )
                }
              >
                +
              </button>

              <button
                disabled={item.quantity <= 1}
                onClick={() =>
                  handleUpdate(
                    item.product_id,
                    item.quantity - 1
                  )
                }
              >
                -
              </button>

              <button
                onClick={() =>
                  handleRemove(item.product_id)
                }
              >
                Remove
              </button>

              <hr />
            </div>
          ))}

          <button
            onClick={handlePlaceOrder}
            disabled={placingOrder}
          >
            {placingOrder
              ? "Placing Order..."
              : "Place Order"}
          </button>
        </>
      )}

      {orderMessage && (
        <p>{orderMessage}</p>
      )}
    </section>
  );
}

export default Cart;
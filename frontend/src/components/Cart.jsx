import { useEffect, useState } from "react";
import {
  getCart,
  updateCart,
  removeFromCart,
} from "../api/cart";

function Cart() {
  const [cart, setCart] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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
        cart.map((item) => (
          <div key={item.id}>
            <p>
              <strong>Product ID:</strong> {item.product_id}
            </p>

            <p>
              <strong>Quantity:</strong> {item.quantity}
            </p>

            <button
              onClick={() =>
                handleUpdate(item.product_id, item.quantity + 1)
              }
            >
              +
            </button>

            <button
              disabled={item.quantity <= 1}
              onClick={() =>
                handleUpdate(item.product_id, item.quantity - 1)
              }
            >
              -
            </button>

            <button
              onClick={() => handleRemove(item.product_id)}
            >
              Remove
            </button>

            <hr />
          </div>
        ))
      )}
    </section>
  );
}

export default Cart;
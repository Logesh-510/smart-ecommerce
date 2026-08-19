import { useEffect, useState } from "react";
import api from "../api/api";
import { addToCart } from "../api/cart";

function Products() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/products/")
      .then((response) => {
        setProducts(response.data);
      })
      .catch((error) => {
        console.error(error);
        setError("Unable to load products");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

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

  if (loading) {
    return <p>Loading products...</p>;
  }

  if (error) {
    return <p>{error}</p>;
  }

  return (
    <section>
      <h2>Products</h2>

      {products.length === 0 ? (
        <p>No products available.</p>
      ) : (
        products.map((product) => (
          <div key={product.id}>
            <h3>{product.name}</h3>

            <p>{product.description}</p>

            <p>Category: {product.category}</p>

            <p>
              Price: ₹
              {Number(product.price).toLocaleString("en-IN")}
            </p>

            <p>Stock: {product.stock}</p>

            <p>Popularity: {product.popularity}</p>

            <button
              onClick={() => handleAddToCart(product.id)}
            >
              Add to Cart
            </button>

            <hr />
          </div>
        ))
      )}
    </section>
  );
}

export default Products;
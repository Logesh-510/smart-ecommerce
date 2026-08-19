import api from "./api";
import { getAccessToken } from "./auth";

function authConfig() {
  return {
    headers: {
      Authorization: `Bearer ${getAccessToken()}`,
    },
  };
}

export async function getCart() {
  const response = await api.get("/cart", authConfig());
  return response.data;
}

export async function addToCart(product_id, quantity = 1) {
  const response = await api.post(
    "/cart",
    {
      product_id,
      quantity,
    },
    authConfig()
  );

  return response.data;
}

export async function updateCart(product_id, quantity) {
  const response = await api.put(
    `/cart/${product_id}`,
    {
      quantity,
    },
    authConfig()
  );

  return response.data;
}

export async function removeFromCart(product_id) {
  const response = await api.delete(
    `/cart/${product_id}`,
    authConfig()
  );

  return response.data;
}
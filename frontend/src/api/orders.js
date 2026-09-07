import api from "./api";

export async function createOrder() {
  const response = await api.post("/orders");
  return response.data;
}

export async function getMyOrders() {
  const response = await api.get("/orders");
  return response.data;
}
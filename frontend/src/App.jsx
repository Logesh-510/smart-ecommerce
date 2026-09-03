import Products from "./components/Products";
import Cart from "./components/Cart";
import Login from "./components/Login";
import Orders from "./components/Orders";

function App() {
  return (
    <div>
      <h1>Smart E-Commerce</h1>

      <Login />

      <Products />

      <Cart />

      <Orders />
    </div>
  );
}

export default App;
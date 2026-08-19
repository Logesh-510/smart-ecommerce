import Products from "./components/Products";
import Cart from "./components/Cart";
import Login from "./components/Login";

function App() {
  return (
    <div>
      <h1>Smart E-Commerce</h1>

      <Login />

      <Products />

      <Cart />
    </div>
  );
}

export default App;
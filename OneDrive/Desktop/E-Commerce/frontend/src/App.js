// App.js
import React from 'react';
import Navbar from './Components/navbar/navbar';
import { BrowserRouter,Routes,Route} from 'react-router-dom';
import './App.css';
import ShopCategory from './pages/ShopCategory';
import Product from './pages/Product';
import Cart from './pages/Cart';
import LoginSignup from './pages/LoginSignup';
import Shop from './pages/Shop.jsx';
import Footer from './Components/Footer/Footer.jsx';


function App() {
  return (
    <div className="App">
      <BrowserRouter>
      <Navbar/>
      <Routes>
        <Route path="/" element={<Shop/>}/>
        <Route path="/mens" element={<ShopCategory category="Men"/>}/> 
        <Route path="/womens" element={<ShopCategory category="Women"/>}/> 
        <Route path="/kids" element={<ShopCategory category="Kids"/>}/> 
        <Route path="/product" element={<Product/>}> 
          <Route path=":productId" element={<Product/>}/> 
        </Route>
        <Route path="/cart" element={<Cart/>}/>
        <Route path="/login" element={<LoginSignup/>}/>
      </Routes>
      </BrowserRouter>
      <Footer/>
    </div>
  );
}

export default App;

import React from 'react'

import ReactDOM from 'react-dom/client'
import App from './App.tsx'

import { BrowserRouter, Route, Routes } from "react-router-dom";
import NotFound from './pages/notfound.tsx'
import AppBar from './components/appbar.tsx'
import Home from './pages/home.jsx'
import './styles/css/index.css'
import  About  from './pages/about.jsx';
import PrivacyPolicy from './pages/privacy_policy.jsx';
import Navbar from './components/navbar';


ReactDOM.createRoot((document.getElementById('root'))).render(
  <React.StrictMode>
   <AppBar>
    <BrowserRouter>
    
    <Routes>
      
      <Route index element={<App/>}/>

      <Route path='/home' element={<Home/>}/>

      <Route path='*' element={<NotFound/>}/>
      <Route path = '/about' element={<About/>}/>
      <Route path = '/privacypolicy' element={<PrivacyPolicy/>}/>
    </Routes>
    </BrowserRouter>
    </AppBar>
  </React.StrictMode>,
)


import React from 'react'

import ReactDOM from 'react-dom/client'
import App from './App.tsx'

import { BrowserRouter, Route, Routes } from 'react-router'
import NotFound from './pages/notfound.tsx'
import AppBar from './components/appbar.tsx'
import Home from './pages/home.jsx'
import './styles/css/index.css'



ReactDOM.createRoot((document.getElementById('root'))).render(
  <React.StrictMode>
   <AppBar>
    <BrowserRouter>
    
    <Routes>
      
      <Route index element={<App/>}/>

      <Route path='/home' element={<Home/>}/>

      <Route path='*' element={<NotFound/>}/>
    </Routes>
    </BrowserRouter>
    </AppBar>
  </React.StrictMode>,
)


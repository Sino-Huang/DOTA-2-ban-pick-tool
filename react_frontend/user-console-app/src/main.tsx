import React from 'react'
import ReactDOM from 'react-dom/client'
// reset css 
import 'reset-css'

// import global 
import '@/assets/styles/global.scss'

import App from './App.tsx'

import { createBrowserRouter, RouterProvider } from "react-router-dom"

const router = createBrowserRouter(
  [
    {
      path: "/",
      element: <App/>
    },
  ]
)

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RouterProvider router={router}/>
  </React.StrictMode>,
)

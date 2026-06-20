import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import Runes from './pages/Runes'
import Sources from './pages/Sources'
import Methodology from './pages/Methodology'
import './App.css'

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/runes" element={<Runes />} />
          <Route path="/sources" element={<Sources />} />
          <Route path="/about-methodology" element={<Methodology />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

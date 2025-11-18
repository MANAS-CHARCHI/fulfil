import { useState } from 'react'
import './App.css'
import CSVImporter from './components/CSVImporter'

function App() {
  const [count, setCount] = useState(0)

  return (
    <><CSVImporter /></>
  )
}

export default App

import '../globals.css'

interface ProductCardProps {
  name: string
  amount: string
  icon: string
}

export default function ProductCard({ name, amount, icon }: ProductCardProps) {
  return (
    <div className="product-card">
      <span className="product-icon">{icon}</span>
      <div className="product-info">
        <h4>{name}</h4>
        <p>{amount}</p>
      </div>
    </div>
  )
}





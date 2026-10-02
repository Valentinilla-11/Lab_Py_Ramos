from database import Cart

# Función auxiliar para calcular el total del carrito
def calculate_cart_total(cart: Cart) -> float:
    if not cart or not cart.products:
        return 0.0
    return sum(
        item.product.price * item.quantity 
        for item in cart.products 
        if item.product
    )
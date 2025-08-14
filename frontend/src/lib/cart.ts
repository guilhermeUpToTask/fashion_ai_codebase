export interface CartItem {
  id: string;
  name: string;
  price: string;
  quantity: number;
  image?: string;
  sku?: string;
}

export interface Cart {
  items: CartItem[];
  total: number;
  itemCount: number;
}

const CART_STORAGE_KEY = 'fashion_cart';

export const getCart = (): Cart => {
  if (typeof window === 'undefined') {
    return { items: [], total: 0, itemCount: 0 };
  }
  
  try {
    const stored = localStorage.getItem(CART_STORAGE_KEY);
    return stored ? JSON.parse(stored) : { items: [], total: 0, itemCount: 0 };
  } catch {
    return { items: [], total: 0, itemCount: 0 };
  }
};

export const saveCart = (cart: Cart): void => {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));
  } catch (error) {
    console.error('Failed to save cart:', error);
  }
};

export const addToCart = (product: Omit<CartItem, 'quantity'>): Cart => {
  const cart = getCart();
  const existingItem = cart.items.find(item => item.id === product.id);
  
  if (existingItem) {
    existingItem.quantity += 1;
  } else {
    cart.items.push({ ...product, quantity: 1 });
  }
  
  const updatedCart = {
    ...cart,
    total: cart.items.reduce((sum, item) => sum + parseFloat(item.price) * item.quantity, 0),
    itemCount: cart.items.reduce((sum, item) => sum + item.quantity, 0),
  };
  
  saveCart(updatedCart);
  return updatedCart;
};

export const removeFromCart = (productId: string): Cart => {
  const cart = getCart();
  const updatedItems = cart.items.filter(item => item.id !== productId);
  
  const updatedCart = {
    items: updatedItems,
    total: updatedItems.reduce((sum, item) => sum + parseFloat(item.price) * item.quantity, 0),
    itemCount: updatedItems.reduce((sum, item) => sum + item.quantity, 0),
  };
  
  saveCart(updatedCart);
  return updatedCart;
};

export const updateCartItemQuantity = (productId: string, quantity: number): Cart => {
  const cart = getCart();
  
  if (quantity <= 0) {
    return removeFromCart(productId);
  }
  
  const updatedItems = cart.items.map(item =>
    item.id === productId ? { ...item, quantity } : item
  );
  
  const updatedCart = {
    items: updatedItems,
    total: updatedItems.reduce((sum, item) => sum + parseFloat(item.price) * item.quantity, 0),
    itemCount: updatedItems.reduce((sum, item) => sum + item.quantity, 0),
  };
  
  saveCart(updatedCart);
  return updatedCart;
};

export const clearCart = (): Cart => {
  const emptyCart = { items: [], total: 0, itemCount: 0 };
  saveCart(emptyCart);
  return emptyCart;
}; 
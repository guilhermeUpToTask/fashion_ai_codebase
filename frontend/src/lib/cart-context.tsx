import { createContext, type ReactNode } from 'react';

interface CartContextType {
  itemCount: number;
}

const CartContext = createContext<CartContextType>({ itemCount: 0 });

export const CartProvider = ({ children }: { children: ReactNode }) => {
  return (
    <CartContext.Provider value={{ itemCount: 0 }}>
      {children}
    </CartContext.Provider>
  );
}; 
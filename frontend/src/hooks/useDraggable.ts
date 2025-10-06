import { useState, useRef, useEffect, MouseEvent } from 'react';

interface Position {
  x: number;
  y: number;
}

interface UseDraggableReturn {
  position: Position;
  handleMouseDown: (e: MouseEvent) => void;
  isDragging: boolean;
}

/**
 * Custom hook to make elements draggable
 * Returns position and mouse down handler
 */
export function useDraggable(initialX: number = 0, initialY: number = 0): UseDraggableReturn {
  const [position, setPosition] = useState<Position>({ x: initialX, y: initialY });
  const [isDragging, setIsDragging] = useState(false);
  const dragStart = useRef<Position>({ x: 0, y: 0 });
  const elementStart = useRef<Position>({ x: initialX, y: initialY });

  const handleMouseDown = (e: MouseEvent) => {
    // Only allow dragging from the header area (not from interactive elements)
    const target = e.target as HTMLElement;
    if (
      target.tagName === 'BUTTON' || 
      target.closest('button') ||
      target.tagName === 'INPUT' ||
      target.closest('input') ||
      target.tagName === 'CANVAS' ||
      target.closest('canvas')
    ) {
      return; // Don't start drag if clicking on interactive elements
    }

    setIsDragging(true);
    dragStart.current = { x: e.clientX, y: e.clientY };
    elementStart.current = position;
    e.preventDefault();
  };

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: globalThis.MouseEvent) => {
      const deltaX = e.clientX - dragStart.current.x;
      const deltaY = e.clientY - dragStart.current.y;

      setPosition({
        x: elementStart.current.x + deltaX,
        y: elementStart.current.y + deltaY,
      });
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

  return { position, handleMouseDown, isDragging };
}






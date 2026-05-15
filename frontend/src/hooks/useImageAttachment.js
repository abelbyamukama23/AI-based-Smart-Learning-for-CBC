import { useState, useRef, useEffect } from "react";

/**
 * Hook for handling image attachments with preview generation and memory cleanup.
 * @returns {object} { imageFile, imagePreview, imageInputRef, handleImageChange, clearImage }
 */
export function useImageAttachment() {
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const imageInputRef = useRef(null);

  // Cleanup ObjectURL to prevent memory leaks
  useEffect(() => {
    return () => {
      if (imagePreview) URL.revokeObjectURL(imagePreview);
    };
  }, [imagePreview]);

  const clearImage = () => {
    if (imagePreview) URL.revokeObjectURL(imagePreview);
    setImageFile(null);
    setImagePreview(null);
    if (imageInputRef.current) {
      imageInputRef.current.value = "";
    }
  };

  const handleImageChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    if (imagePreview) URL.revokeObjectURL(imagePreview);
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
  };

  return {
    imageFile,
    imagePreview,
    imageInputRef,
    handleImageChange,
    clearImage,
  };
}

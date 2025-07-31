import React from "react";

const Loader = ({ text = "Loading..." }) => {
  return (
    <div className="flex items-center justify-center min-h-screen bg-white">
      <div className="flex flex-col items-center">
        <div className="w-16 h-16 border-4 border-primaryGreen border-t-transparent rounded-full animate-spin"></div>
        <p className="mt-4 text-lg text-primaryGreen font-medium">{text}</p>
      </div>
    </div>
  );
};

export default Loader;

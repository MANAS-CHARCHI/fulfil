import React, { useState } from "react";

import CSVImporter from "../pages/CSVImporter";
import ProductDetailsPage from "../pages/ProductDetails";

// // Dummy components for each tab content
// const UploadPage = () => <CSVImporter />;
// const ProductDetailsPage = () => <ProductDetailsPage />;
// const WebhookPage = () => <div className="p-4">Webhook Content</div>;

const Header = () => {
    const [activeTab, setActiveTab] = useState("upload");

    const renderContent = () => {
        switch (activeTab) {
            case "upload":
                return <CSVImporter />;
            case "product":
                return <ProductDetailsPage />;
            case "webhook":
                return <>hi</>;
            default:
                return null;
        }
    };

    return (
        <div>
            {/* Header Tabs */}
            <div className="bg-white shadow-md p-4 flex justify-start space-x-4">
                <button
                    onClick={() => setActiveTab("upload")}
                    className={`px-4 py-2 rounded-md font-medium ${activeTab === "upload"
                        ? "bg-blue-500 text-white"
                        : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                        }`}
                >
                    Upload
                </button>
                <button
                    onClick={() => setActiveTab("product")}
                    className={`px-4 py-2 rounded-md font-medium ${activeTab === "product"
                        ? "bg-blue-500 text-white"
                        : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                        }`}
                >
                    Product Details
                </button>
                <button
                    onClick={() => setActiveTab("webhook")}
                    className={`px-4 py-2 rounded-md font-medium ${activeTab === "webhook"
                        ? "bg-blue-500 text-white"
                        : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                        }`}
                >
                    Webhook
                </button>
            </div>

            {/* Tab Content */}
            <div>{renderContent()}</div>
        </div>
    );
};

export default Header;

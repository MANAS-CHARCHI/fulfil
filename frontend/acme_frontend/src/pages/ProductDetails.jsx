import React, { useEffect, useState } from "react";

const ProductDetailsPage = () => {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(false);
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize, setPageSize] = useState(10);
    const [totalPages, setTotalPages] = useState(1);
    const [totalItems, setTotalItems] = useState(0);

    const [skuFilter, setSkuFilter] = useState("");
    const [activeFilter, setActiveFilter] = useState("all");

    const fetchStream = async (page = 1) => {
        setLoading(true);
        setProducts([]);

        try {
            const params = new URLSearchParams();
            params.append("page", page);
            params.append("limit", pageSize);
            if (skuFilter) params.append("sku", skuFilter);
            if (activeFilter !== "all") params.append("active", activeFilter);

            const response = await fetch(
                `http://localhost:5000/products/devices/stream/?${params.toString()}`
            );

            if (!response.body) {
                console.error("Streaming not supported in this browser.");
                return;
            }

            // Read total count header
            const totalCount = response.headers.get("X-Total-Count");
            if (totalCount) {
                setTotalItems(Number(totalCount));
                setTotalPages(Math.ceil(Number(totalCount) / pageSize));
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let buffer = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });

                const lines = buffer.split("\n");
                buffer = lines.pop(); // keep last incomplete line

                for (let line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const product = JSON.parse(line);
                        setProducts((prev) => [...prev, product]);
                    } catch (err) {
                        console.error("Invalid JSON:", line);
                    }
                }
            }
        } catch (err) {
            console.error("Failed to fetch devices:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStream(currentPage);
    }, [currentPage, pageSize, skuFilter, activeFilter]);

    const handlePrev = () => {
        if (currentPage > 1) setCurrentPage((prev) => prev - 1);
    };

    const handleNext = () => {
        if (currentPage < totalPages) setCurrentPage((prev) => prev + 1);
    };

    const formatDate = (timestamp) =>
        timestamp ? new Date(timestamp).toLocaleString() : "";

    const startItem = (currentPage - 1) * pageSize + 1;
    const endItem = Math.min(currentPage * pageSize, totalItems);
    const toggleActiveStatus = async (productId, newStatus) => {
        try {
            const response = await fetch(
                `http://localhost:5000/products/device/${productId}/update-status/`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ active: newStatus }),
                }
            );

            if (!response.ok) {
                console.error("Failed to update status");
                return;
            }

            const data = await response.json();

            // Update state so UI reflects new status immediately
            setProducts((prev) =>
                prev.map((p) => (p.id === data.id ? { ...p, active: data.active } : p))
            );
        } catch (err) {
            console.error("Error updating status:", err);
        }
    };

    return (
        <div className="p-4">

            {/* Filters */}
            <div className="flex gap-4 mb-4">
                <input
                    type="text"
                    placeholder="Filter by SKU"
                    value={skuFilter}
                    onChange={(e) => setSkuFilter(e.target.value)}
                    className="border px-2 py-1 rounded"
                />
                <select
                    value={activeFilter}
                    onChange={(e) => setActiveFilter(e.target.value)}
                    className="border px-2 py-1 rounded"
                >
                    <option value="all">All</option>
                    <option value="true">Active</option>
                    <option value="false">Inactive</option>
                </select>
                <input
                    type="number"
                    min={1}
                    value={pageSize}
                    onChange={(e) => setPageSize(Number(e.target.value))}
                    placeholder="Page size"
                    className="border px-2 py-1 rounded w-24"
                />
            </div>

            {/* Info about current slice */}
            <p>
                Showing items {startItem} – {endItem} of {totalItems}
            </p>

            {/* Table */}
            <table className="min-w-full border border-gray-300">
                <thead>
                    <tr className="bg-gray-200">
                        <th className="border px-4 py-2">Name</th>
                        <th className="border px-4 py-2">SKU</th>
                        <th className="border px-4 py-2">Description</th>
                        <th className="border px-4 py-2">Active</th>
                        <th className="border px-4 py-2">Created At</th>
                        <th className="border px-4 py-2">Updated At</th>
                    </tr>
                </thead>
                <tbody>
                    {products.map((p, idx) => (
                        <tr key={idx}>
                            <td className="border px-4 py-2">{p.name}</td>
                            <td className="border px-4 py-2">{p.sku}</td>
                            <td className="border px-4 py-2">{p.description}</td>
                            <td className="border px-4 py-2 text-center">
                                <input
                                    type="checkbox"
                                    checked={p.active}
                                    onChange={() => toggleActiveStatus(p.id, !p.active)}
                                />
                            </td>

                            <td className="border px-4 py-2">{formatDate(p.created_at)}</td>
                            <td className="border px-4 py-2">{formatDate(p.updated_at)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>

            {/* Pagination */}
            <div className="mt-4 flex justify-between items-center">
                <button
                    onClick={handlePrev}
                    disabled={currentPage === 1}
                    className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50"
                >
                    Previous
                </button>
                <span>
                    Page {currentPage} of {totalPages} ({startItem}-{endItem})
                </span>
                <button
                    onClick={handleNext}
                    disabled={currentPage === totalPages}
                    className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50"
                >
                    Next
                </button>
            </div>

            {loading && products.length > 0 && <p className="mt-2">Streaming data for this page...</p>}
        </div>
    );
};

export default ProductDetailsPage;

import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";

const PaymentSection = ({ cartId, setCartId, setSection }) => {
    const [selectedPaymentMethod, setSelectedPaymentMethod] = useState("");
    const [orderId, setOrderId] = useState(null);
    const [razorpayInstance, setRazorpayInstance] = useState(null);
    const [forceUpdate, setForceUpdate] = useState(false);
    const [isPlacingOrder, setIsPlacingOrder] = useState(false);
    const [showSuccessPopup, setShowSuccessPopup] = useState(false);
    const [isRazorpayLoaded, setIsRazorpayLoaded] = useState(false);
    
    const { accessToken } = useSelector((state) => state.auth);
    const shopOrder = useSelector((state) => state.shoporder.order);
    const navigate = useNavigate();

    // Load Razorpay script
    useEffect(() => {
        const script = document.createElement("script");
        script.src = "https://checkout.razorpay.com/v1/checkout.js";
        script.async = true;
        script.onload = () => setIsRazorpayLoaded(true);
        document.body.appendChild(script);

        return () => {
            document.body.removeChild(script);
            // Clean up Razorpay instance
            if (razorpayInstance) {
                razorpayInstance.close();
            }
        };
    }, []);

    useEffect(() => {
        setSection("payment");
    }, [setSection]);

    const handleNavigate = (view) => {
        navigate("/profile", { state: { currentView: view } });
    };

    const handlePlaceOrder = async () => {
        if (!cartId) {
            console.error("No cart ID available");
            return;
        }
        
        setIsPlacingOrder(true);
        try {
            const paymentDetails = {
                transaction_id: `COD_${Date.now()}`,
                status: "pending",
                amount: shopOrder.orderTotal.toFixed(2),
                currency: "INR",
                payment_method: "cod",
                tracking_id: `COD_${Date.now()}`,
                gateway_response: { 
                    payment_id: `cod_${Date.now()}`, 
                    order_id: `cod_${Date.now()}`, 
                    signature: `cod_${Date.now()}` 
                },
                platform_fee: shopOrder.platformfee.toFixed(2),
                shipping_cost: shopOrder.shippingfee.toFixed(2),
                seller_payout: (shopOrder.orderTotal - (shopOrder.platformfee || 0)).toFixed(2),
            };

            await savePaymentDetails(paymentDetails);
        } catch (error) {
            console.error("Error placing COD order:", error);
        } finally {
            setIsPlacingOrder(false);
        }
    };

    const savePaymentDetails = async (paymentDetails) => {
        try {
            const response = await fetch(
                `https://127.0.0.1:8000/api/save-payment-details/${cartId}/`,
                {
                    method: "POST",
                    headers: {
                        Authorization: `Bearer ${accessToken}`,
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(paymentDetails),
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            setCartId(null);
            console.log("Payment details saved successfully:", data);
            console.log("POPOPOPPIIIDD", data.payment_id);
            
            if (data.payment_id) {
                await generateBill(data.payment_id);
            } else {
                setShowSuccessPopup(true);
            }
        } catch (error) {
            console.error("Error saving payment details:", error);
            throw error;
        }
    };

    const generateBill = async (paymentId) => {
        try {
            const response = await fetch(
                "https://127.0.0.1:8000/api/generate-bill/",
                {
                    method: "POST",
                    headers: {
                        Authorization: `Bearer ${accessToken}`,
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ payment_id: paymentId }),
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            await response.json();
            setShowSuccessPopup(true);
        } catch (error) {
            console.error("Error generating bill:", error);
            throw error;
        }
    };

    const handleRazorpayPayment = async () => {
        if (!isRazorpayLoaded) {
            console.error("Razorpay script not loaded yet");
            return;
        }

        try {
            const response = await fetch(
                "https://127.0.0.1:8000/api/create-razorpay-order/",
                {
                    method: "POST",
                    headers: {
                        Authorization: `Bearer ${accessToken}`,
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        amount: shopOrder.orderTotal.toFixed(2),
                    }),
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            setOrderId(data.order_id);

            const options = {
                key: "rzp_test_wHEa0EziyINW42",
                amount: data.amount * 100,
                currency: data.currency,
                order_id: data.order_id, // Use the order_id directly from response
                name: "Fitza",
                description: "Payment for Order",
                handler: async function (response) {
                    const paymentDetails = {
                        transaction_id: response.razorpay_payment_id,
                        status: "completed",
                        amount: data.amount,
                        currency: "INR",
                        payment_method: "razorpay",
                        tracking_id: `TRACK_${response.razorpay_payment_id.slice(0, 10)}`,
                        gateway_response: response,
                        platform_fee: shopOrder.platformfee.toFixed(2),
                        shipping_cost: shopOrder.shippingfee.toFixed(2),
                        seller_payout: (data.amount / 100 - (shopOrder.platformfee || 0)).toFixed(2),
                    };
                    console.log("PAYDEEEEE",paymentDetails);

                    try {
                        await savePaymentDetails(paymentDetails);
                    } catch (error) {
                        console.error("Error processing payment:", error);
                    }
                },
                prefill: {
                    name: data.user?.name || "Customer Name",
                    email: data.user?.email || "customer@example.com",
                    contact: data.user?.phone || "1234567890",
                },
                theme: {
                    color: "#3399cc",
                },
            };

            const rzp = new window.Razorpay(options);
            setRazorpayInstance(rzp);

            rzp.on("payment.failed", (response) => {
                console.error("Payment failed:", response.error);
                resetScroll();
            });

            rzp.on("close", () => {
                resetScroll();
            });

            rzp.open();
        } catch (error) {
            console.error("Payment error:", error);
            resetScroll();
        }
    };

    const resetScroll = () => {
        document.body.style.overflow = "auto";
        document.documentElement.style.overflow = "auto";
        const root = document.getElementById("root");
        if (root) root.style.overflow = "auto";
        setForceUpdate((prev) => !prev);
    };

    const SuccessPopup = () => {
        return (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                <div className="bg-white rounded-xl shadow-2xl max-w-md w-full transform transition-all duration-300 scale-95 hover:scale-100">
                    <button
                        onClick={() => setShowSuccessPopup(false)}
                        className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 transition"
                    >
                        <i className="fa-solid fa-xmark p-2 text-gray-500 text-lg"></i>
                    </button>

                    <div className="p-8 text-center">
                        <div className="flex justify-center mb-6">
                            <div className="relative">
                                <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center">
                                    <i className="fa-solid fa-circle-check text-green-500 text-5xl"></i>
                                </div>
                                <div className="absolute -bottom-2 -right-2 bg-white rounded-full p-2 shadow-md">
                                    <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                                        <i className="fa-solid fa-check text-white text-xs"></i>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <h3 className="text-2xl font-bold text-gray-800 mb-2">Order Placed Successfully!</h3>

                        <p className="text-gray-600 mb-6">
                            Your order has been confirmed. You'll receive an email with the order details shortly.
                        </p>

                        <div className="flex flex-col sm:flex-row gap-4 justify-center">
                            <button
                                onClick={() => handleNavigate("myorders")}
                                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg transition flex items-center justify-center gap-2"
                            >
                                <i className="fa-solid fa-bag-shopping text-white"></i>
                                Track Order
                            </button>
                            <button
                                onClick={() => {
                                    setShowSuccessPopup(false);
                                    navigate("/");
                                }}
                                className="flex-1 border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium py-3 px-6 rounded-lg transition"
                            >
                                Continue Shopping
                            </button>
                        </div>

                        <div className="mt-6 pt-6 border-t border-gray-100">
                            <p className="text-sm text-gray-500">
                                Need help?{" "}
                                <a href="/contact" className="text-blue-600 hover:underline">
                                    Contact us
                                </a>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col lg:flex-row gap-8 p-6 lg:px-[200px] lg:p-10">
            <div className="bg-white shadow-lg rounded-lg flex-1 p-6">
                <h1 className="text-2xl font-bold text-gray-800 mb-6">Select Payment Method</h1>
                <div className="space-y-6">
                    <div
                        className={`flex items-center justify-between bg-gray-100 p-4 rounded-lg shadow hover:shadow-lg transition ${
                            selectedPaymentMethod === "cod" ? "ring-2 ring-blue-500" : ""
                        }`}
                        onClick={() => setSelectedPaymentMethod("cod")}
                    >
                        <div>
                            <h2 className="text-lg font-semibold text-gray-700">Cash On Delivery</h2>
                            <p className="text-gray-600 text-sm">Price: ₹{shopOrder?.orderTotal?.toFixed(2) || "0.00"}</p>
                        </div>
                        {selectedPaymentMethod === "cod" ? (
                            <button
                                className="bg-blue-600 text-white px-4 py-2 rounded-lg shadow hover:bg-blue-700"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handlePlaceOrder();
                                }}
                                disabled={isPlacingOrder}
                            >
                                {isPlacingOrder ? "Placing Order..." : "Place Order"}
                            </button>
                        ) : (
                            <input
                                type="radio"
                                name="payment-method"
                                className="w-5 h-5 accent-blue-600"
                                checked={selectedPaymentMethod === "cod"}
                                readOnly
                            />
                        )}
                    </div>
                    <div
                        className={`flex items-center justify-between bg-gray-100 p-4 rounded-lg shadow hover:shadow-lg transition ${
                            selectedPaymentMethod === "online" ? "ring-2 ring-blue-500" : ""
                        }`}
                        onClick={() => setSelectedPaymentMethod("online")}
                    >
                        <div>
                            <h2 className="text-lg font-semibold text-gray-700">Pay Online</h2>
                            <p className="text-gray-600 text-sm">Price: ₹{shopOrder?.orderTotal?.toFixed(2) || "0.00"}</p>
                        </div>
                        <input
                            type="radio"
                            name="payment-method"
                            className="w-5 h-5 accent-blue-600"
                            checked={selectedPaymentMethod === "online"}
                            readOnly
                        />
                    </div>

                    {selectedPaymentMethod === "online" && (
                        <div className="mt-6 bg-white p-4 rounded-lg shadow-lg">
                            <h2 className="text-lg font-semibold text-gray-700 mb-4">Pay Online via Razorpay</h2>
                            <button
                                className="bg-blue-600 text-white px-4 py-2 rounded-lg shadow hover:bg-blue-700"
                                onClick={handleRazorpayPayment}
                                disabled={!isRazorpayLoaded}
                            >
                                {isRazorpayLoaded ? "Proceed to Payment" : "Loading Payment..."}
                            </button>
                        </div>
                    )}
                </div>
            </div>
            
            <div className="bg-white shadow-lg rounded-lg p-6 w-full lg:w-1/3">
                <h2 className="text-xl font-semibold text-gray-800 mb-4">Price Details</h2>

                <div className="border-b pb-4 mb-4 space-y-3">
                    <div className="flex justify-between">
                        <span className="text-gray-600">Total MRP</span>
                        <span className="text-gray-800 font-medium">
                            {shopOrder?.productdiscount > 0
                                ? `₹${(shopOrder?.totalmrp + shopOrder?.productdiscount).toFixed(2)}`
                                : `₹${shopOrder?.totalmrp?.toFixed(2) || "0.00"}`}
                        </span>
                    </div>

                    {shopOrder?.productdiscount > 0 && (
                        <div className="flex justify-between">
                            <span className="text-gray-600">Product Discount</span>
                            <span className="text-green-600 font-medium">- ₹{shopOrder?.productdiscount?.toFixed(2) || "0.00"}</span>
                        </div>
                    )}

                    <div className="flex justify-between">
                        <span className="text-gray-600">Shipping Fee</span>
                        <span className="text-gray-800 font-medium">
                            {shopOrder?.shippingfee > 0 ? `₹${shopOrder?.shippingfee?.toFixed(2) || "0.00"}` : "FREE"}
                        </span>
                    </div>

                    <div className="flex justify-between">
                        <span className="text-gray-600">Platform Fee</span>
                        <span className="text-gray-800 font-medium">₹{shopOrder?.platformfee?.toFixed(1) || "0.0"}</span>
                    </div>

                    {shopOrder?.couponapplied && shopOrder.couponapplied !== 0 && (
                        <div className="flex justify-between">
                            <span className="text-gray-600">Coupon Applied</span>
                            <span className="text-green-600 font-medium">- {shopOrder.couponapplied}</span>
                        </div>
                    )}

                    {shopOrder?.discountcard > 0 && (
                        <div className="flex justify-between">
                            <span className="text-gray-600">Card Discount</span>
                            <span className="text-green-600 font-medium">
                                ₹-{(
                                    (shopOrder?.totalmrp + (shopOrder?.productdiscount || 0)) *
                                    (shopOrder?.discountcard / 100)
                                ).toFixed(2)}
                            </span>
                        </div>
                    )}
                </div>

                <div className="flex justify-between pt-4 border-t">
                    <span className="text-lg font-bold text-gray-800">Order Total</span>
                    <span className="text-lg font-bold text-gray-800">
                        ₹{shopOrder?.orderTotal?.toFixed(2) || "0.00"}
                    </span>
                </div>
            </div>

            {showSuccessPopup && <SuccessPopup />}
        </div>
    );
};

export default PaymentSection;







// <!doctype html>
// <html lang="en">
//   <head>
//     <meta charset="UTF-8" />
//     <link rel="icon" type="image/svg+xml" href="/src/assets/fitzaapp.png" />
//     <meta name="viewport" content="width=device-width, initial-scale=1.0" />
//     <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css">
    
//     <title>Fitza</title>
//   </head>
//   <body>
//       <!-- Tidio Chat Widget -->
//     <script src="//code.tidio.co/oq4cz2psg530tohfwarvixcwmz0oxvnb.js" async></script>
//     <div id="root"></div>
//     <!-- <script src="https://checkout.razorpay.com/v1/checkout.js"></script> -->
//     <script type="module" src="/src/main.jsx"></script>
//   </body>
// </html>
// import { kioskAttendanceApp } from '@hr_attendance/public_kiosk/public_kiosk_app';
// import { rpc } from "@web/core/network/rpc";

// class kioskAttendanceAppWithLocationRestriction extends kioskAttendanceApp {
//     async makeRpcWithGeolocation(route, params) {
//         const definedLatitude = -7.9212053; // Lintang tengah lokasi yang diizinkan
//         const definedLongitude = 112.6189918; // Bujur tengah lokasi yang diizinkan
//         const definedRadius = 500; // Radius dalam meter

//         const calculateDistance = (lat1, lon1, lat2, lon2) => {
//             const R = 6371e3; // Radius Bumi dalam meter
//             const toRadians = (deg) => (deg * Math.PI) / 180;

//             const φ1 = toRadians(lat1);
//             const φ2 = toRadians(lat2);
//             const Δφ = toRadians(lat2 - lat1);
//             const Δλ = toRadians(lon2 - lon1);

//             const a =
//                 Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
//                 Math.cos(φ1) * Math.cos(φ2) *
//                 Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
//             const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

//             return R * c; // Jarak dalam meter
//         };

//         return new Promise((resolve, reject) => {
//             if (!navigator.geolocation) {
//                 this.displayNotification("Geolocation is not supported by this browser.");
//                 return reject("Geolocation not supported");
//             }

//             navigator.geolocation.getCurrentPosition(
//                 async ({ coords: { latitude, longitude } }) => {
//                     const distance = calculateDistance(
//                         definedLatitude,
//                         definedLongitude,
//                         latitude,
//                         longitude
//                     );

//                     if (distance > definedRadius) {
//                         this.displayNotification("You are outside the allowed location radius. Attendance cancelled.");
//                         return reject("Out of allowed radius");
//                     }

//                     const result = await rpc(route, {
//                         ...params,
//                         latitude,
//                         longitude,
//                     });
//                     resolve(result);
//                 },
//                 (err) => {
//                     this.displayNotification("Unable to fetch your location. Please try again.");
//                     reject(err);
//                 },
//                 { enableHighAccuracy: true }
//             );
//         });
//     }
// }

// export default kioskAttendanceAppWithLocationRestriction;

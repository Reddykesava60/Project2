// (async () => {
//   const open = (await import("open")).default;
//
//   setTimeout(() => {
//     open("http://localhost:3000/r/italian-place");
//     open("http://localhost:3000/login");
//     open("http://localhost:3000/owner");
//     open("http://localhost:3000/staff");
//     open("http://localhost:3000/admin");
//   }, 5000);
// })();
const { exec } = require("child_process");

setTimeout(() => {
  exec("start http://localhost:3000/r/italian-place");
  exec("start http://localhost:3000/login");
  exec("start http://localhost:3000/owner");
  exec("start http://localhost:3000/staff");
  exec("start http://localhost:3000/admin");
}, 5000);

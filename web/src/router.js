/**
 * router.js — 拦截所有内部链接，改为 hash 导航
 * 每个 Stitch 页面在 <head> 里引入即可
 */
(function () {
  document.addEventListener('DOMContentLoaded', function () {
    document.addEventListener('click', function (e) {
      var a = e.target.closest('a');
      if (!a) return;
      var href = a.getAttribute('href');
      if (!href) return;
      // 只拦截同域的路径型链接（不是外部链接，不是 hash，不是 mailto: 等）
      if (
        href.startsWith('/') &&
        !href.startsWith('//') &&
        !href.match(/^https?:/)
      ) {
        e.preventDefault();
        var hash = '/' + href.replace(/^\//, '');
        window.location.hash = hash;
      }
    });
  });
})();

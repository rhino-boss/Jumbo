/* 倍率線型縱軸縮放（2026-11-09 使用者定）：每種線型只畫一張，滑鼠滾輪縮放縱軸、雙擊還原。
   作用在 .chart[data-hover] 的靜態 SVG：依 data-hover 的數值重畫各線、點與橫向格線。
   與報告內建的滑鼠提示共用同一個資料物件（ch._hd），縮放後提示的圓點位置跟著對。 */
(function(){
  var NS='http://www.w3.org/2000/svg';
  function nice(x){var p=Math.pow(10,Math.floor(Math.log10(x))),m=x/p;return (m<=1?1:m<=2?2:m<=2.5?2.5:m<=5?5:10)*p}
  function fmt(v){var s=+v.toPrecision(6);return s+'%'}
  document.querySelectorAll('.chart[data-hover]').forEach(function(ch){
    var d=ch._hd||(ch._hd=JSON.parse(ch.dataset.hover)),svg=ch.querySelector('svg');if(!svg)return;
    var y0=d.ymax,base=d.t+d.ih,X=function(i){return d.l+i/(d.labels.length-1)*d.iw};
    // 縱軸標題拿掉「固定 0–x%」
    svg.querySelectorAll('text').forEach(function(t){if(/固定/.test(t.textContent))t.textContent=t.textContent.replace(/（固定[^）]*）/,'')});
    // 舊的橫向格線與縱軸刻度
    var grid=[].slice.call(svg.querySelectorAll('line')).filter(function(l){return +l.getAttribute('x1')===d.l&&+l.getAttribute('x2')===d.l+d.iw});
    var ylab=[].slice.call(svg.querySelectorAll('text[text-anchor="end"]')).filter(function(t){return t.hasAttribute('x')&&!t.hasAttribute('transform')});
    var first=grid[0];grid.concat(ylab).forEach(function(n){n.remove()});
    var axis=document.createElementNS(NS,'g');svg.insertBefore(axis,svg.querySelector('g.ser')||null);
    function draw(ym){
      d.ymax=ym;var Y=function(v){return base-v/ym*d.ih};
      var step=nice(ym/5),h='';
      // 淡淡的格線（直線每個區間一條、橫線每個刻度一條），實線低透明度，和滑鼠提示的虛線區隔
      for(var i=0;i<d.labels.length;i++){var x=X(i).toFixed(1);h+='<line class="gl" x1="'+x+'" x2="'+x+'" y1="'+d.t+'" y2="'+base+'"/>'}
      for(var v=0;v<=ym*1.0001;v+=step){var y=Y(v).toFixed(1);
        h+='<line class="gl" x1="'+d.l+'" x2="'+(d.l+d.iw)+'" y1="'+y+'" y2="'+y+'"/>'+
           '<text fill="var(--ink-3)" font-family="var(--font-mono)" font-size="10.5" text-anchor="end" x="'+(d.l-9)+'" y="'+(+y+3.5)+'">'+fmt(v)+'</text>'}
      axis.innerHTML=h;
      svg.querySelectorAll('g.ser').forEach(function(g){var s=d.series[+g.dataset.k];if(!s)return;
        var path=g.querySelector('path'),cs=g.querySelectorAll('circle');
        if(path)path.setAttribute('d',s.v.map(function(v,i){return (i?'L':'M')+X(i).toFixed(2)+' '+Y(v).toFixed(2)}).join(''));
        cs.forEach(function(c,i){if(i<s.v.length)c.setAttribute('cy',Y(s.v[i]).toFixed(2))})});
    }
    // 放大 x 軸文字後底部要多留空間：viewBox 加高，底部標題往下移
    if(!svg.dataset.tall){var vb=svg.getAttribute('viewBox').split(/\s+/).map(Number);vb[3]+=44;vb[0]-=26;vb[2]+=26;svg.setAttribute('viewBox',vb.join(' '));svg.dataset.tall=1;
      // 縱軸標題往左移，和刻度數字留間隔
      svg.querySelectorAll('text[transform*="rotate(-90)"]').forEach(function(t){var m=/translate\(([\d.]+),/.exec(t.getAttribute('transform'));if(m&&+m[1]<d.l-30)t.setAttribute('transform',t.getAttribute('transform').replace(/translate\([\d.]+,/,'translate(-6,'))});
      svg.querySelectorAll('text[x][y]').forEach(function(t){if(+t.getAttribute('y')>d.t+d.ih+60)t.setAttribute('y',+t.getAttribute('y')+44)})}
    draw(y0);
    svg.addEventListener('wheel',function(e){e.preventDefault();var k=e.deltaY>0?1.25:0.8;draw(Math.min(100,Math.max(0.0005,d.ymax*k)))},{passive:false});
    svg.addEventListener('dblclick',function(){draw(y0)});
  });
  // 操作提示：每個頁簽只在最後一張圖下面放一次（2026-11-09 使用者）
  document.querySelectorAll('.panel').forEach(function(p){
    var cs=p.querySelectorAll('.chart[data-hover]');if(!cs.length||p.querySelector('.yz-hint'))return;
    var s=document.createElement('p');s.className='yz-hint';s.textContent='滾輪縮放縱軸．雙擊還原';cs[cs.length-1].after(s)});
})();

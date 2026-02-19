var w={};
w['cc09a72248122']='violate their obligations under international law';
w['c1b3a7f4d22d7']='nature and function';
w['cbe6cbb116b5e']='universal';
w['c57bfa2907178']='autonomy of law on two grounds';
w['cd1a9a86fa7d6']='\"natural law with a variable content\"';
w['ce35a1af278f8']='civic';
w['ca743ecfd0c8c']='contradicting';
w['ce5ee9f000f01']='moral principles';
w['c44b147f40c10']='equality of resources';
w['cea227cfa0d60']='confers power and imposes duties';
w['cffe812acf619']='the UK Constitution';
w['c2633f0a20105']='mechanical and organic solidarity';
document.addEventListener('DOMContentLoaded',function(){
  document.querySelectorAll('[class^="c"]').forEach(function(el){
    var cls=el.className;
    if(w[cls]){
      var temp=document.createElement('span');
      temp.style.visibility='hidden';
      temp.style.position='absolute';
      temp.style.whiteSpace='nowrap';
      var computed=getComputedStyle(el.parentElement);
      temp.style.fontSize=computed.fontSize;
      temp.style.fontFamily=computed.fontFamily;
      temp.style.lineHeight=computed.lineHeight;
      temp.textContent=w[cls];
      document.body.appendChild(temp);
      el.style.width=temp.offsetWidth+'px';
      document.body.removeChild(temp);
    }
  });
});
var w={};
w['cbbf1ac16b228']='cannot search';
w['cda7571c48b97']='integrity of a';
w['c85518b582367']='arrive at the receiver exactly as they were sent';
w['c5c577bede680']='privacy';
w['c2d4aa9e52e5a']='detects a filled buffer and begins to reject';
w['c1c9ebe799d97']='reliable';
w['c130b8db68cad']='transport layer';
w['ce6f76be7f5fc']='buffer-overflow attack';
w['cde44bae8b879']='does not facilitate vulnerability exploitation';
w['cb0a681a34854']='compiler cannot determine the absolute address';
w['cb5471253219b']='classic security properties';
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
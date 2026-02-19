var w={};
w['cd22a658f42f6']='greatest';
w['c7c3af47b3571']='max(l)';
w['c17ba438db049']='q * 2';
w['cee57e09a7aed']='floor division';
w['c9cf77340b08c']='smallest';
w['c7fb7446daf73']='[\'Hi!\'] * 4';
w['c05752096dcf3']='first element';
w['c21c039033ac0']='a[i] == max';
w['cdede12e6ed9b']='extensive testing';
w['cb894ef532809']='not case-sensitive';
w['c074a5bd4b07a']='first duplicate element';
w['cdbdefd4e37c8']='three closest elements';
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
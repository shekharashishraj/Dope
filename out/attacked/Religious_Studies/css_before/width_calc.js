var w={};
w['c6e5dd58afc74']='Speaking in tongues';
w['c782b3ec0c54b']='world-renouncing';
w['ca190b26e32be']='leader';
w['ce4fa2adc14c7']='Icons are a main feature';
w['c4db43874796a']='the nature of what';
w['c646667e903ea']='Bodu Bala Sena';
w['c3a58b3f53e29']='most important';
w['cf0efacdd653a']='Gemarah';
w['c5e38470c2877']='white-clad';
w['c86be92443d60']='express love and passion';
w['c468bcf707ca1']='Babylonian captivity';
w['c6a34783e2aec']='Flower Sermon';
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
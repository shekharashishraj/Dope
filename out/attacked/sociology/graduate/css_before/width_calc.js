var w={};
w['c39696aeb0033']='because:';
w['c4d30d4c0b2b1']='deviant';
w['ca1341ffdff60']='network organization';
w['c580cfa4a33b1']='collective representations';
w['c59db2cdf66b7']='most relevant';
w['cf11418e5f8e5']='urban areas';
w['ce5d06384ecf3']='all societies';
w['c0122a70f0b21']='Pluralist';
w['c738bdeb93850']='did not include';
w['c5690c76b8459']='socialization';
w['c6f63a7e61692']='functionalist perspective';
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
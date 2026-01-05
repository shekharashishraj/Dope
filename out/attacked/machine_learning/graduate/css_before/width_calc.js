var w={};
w['cbc8187a97c01']='ImageNet has images of various resolutions';
w['cc9b003b48434']='were not initialized';
w['cc3908c58b2eb']='null space';
w['c89fef142bd0c']='zeroed out';
w['c2b592f0c6d23']='Averaging the output';
w['cf605f8f2bd1e']='ResNets';
w['c3c85b7b19ed5']='P(A, B, C)';
w['c3e57342adc54']='fails to capture the underlying patterns';
w['cf595f62441eb']='underfitting and overfitting';
w['c3e9e99ce7d71']='effective';
w['c3165c61a8bf6']='entropy in joint distributions';
w['cc733894333d2']='assumptions of the Naive Bayes classifier';
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
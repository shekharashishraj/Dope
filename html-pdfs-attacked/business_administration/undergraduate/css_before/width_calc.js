var w={};
w['cfd2a9c404bb3']='high levels of business failures and unemployment';
w['ce7c81d747c9d']='when did';
w['c0407eb4dcd21']='spoken endorsement';
w['c4090e1951c37']='the depth and breadth in which these products are stocked';
w['cba6a34cf0da7']='Of what is advertising a form?';
w['c4c8ccc727853']='consumer';
w['cb21a46c49e71']='negatively';
w['cab26fde23f17']='laterally';
w['c7e6a3efc7e1b']='commonly';
w['ca86ccc6a70f4']='physiological';
w['cc8b999d13754']='direct selling';
w['c92edd15568f0']='March (1988)';
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
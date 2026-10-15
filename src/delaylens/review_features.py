"""Event-time historical features and static geographic approximation."""
import numpy as np
import pandas as pd
def history_features(df):
    """Update statistics only when a past delivery strictly precedes approval."""
    df=df.copy().reset_index(drop=True)
    deliveries=df.loc[df.late.notna()].sort_values(['order_delivered_customer_date','order_id']).index.to_numpy()
    durations=(df.order_delivered_customer_date.dt.normalize()-df.order_approved_at.dt.normalize()).dt.days.to_numpy()
    rows=df.to_dict('records'); seller={}; route={}; cursor=0
    global_n=global_days=global_late=0
    out=np.zeros((len(df),6))
    for i in df.sort_values(['order_approved_at','order_id']).index:
        r=rows[i]
        while cursor<len(deliveries) and rows[deliveries[cursor]]['order_delivered_customer_date']<r['order_approved_at']:
            j=deliveries[cursor]; past=rows[j]
            for table,key in [(seller,past['seller_id']),(route,(past['seller_state'],past['customer_state']))]:
                n,d,late=table.get(key,(0,0.,0.))
                table[key]=(n+1,d+durations[j],late+past['late'])
            global_n+=1; global_days+=durations[j]; global_late+=past['late']; cursor+=1
        prior_days=global_days/global_n if global_n else 12.
        prior_late=global_late/global_n if global_n else .08
        values=[]
        for table,key in [(seller,r['seller_id']),(route,(r['seller_state'],r['customer_state']))]:
            n,d,late=table.get(key,(0,0.,0.))
            values += [n,(d+20*prior_days)/(n+20),(late+20*prior_late)/(n+20)]
        out[i]=values
    df[['seller_count','seller_days','seller_late','route_count','route_days','route_late']]=out
    df['seller_slack']=df.promised_days-df.seller_days
    df['route_slack']=df.promised_days-df.route_days
    df['duration_days']=durations
    return df

def add_distance(df,raw):
    geo=pd.read_csv(raw/'olist_geolocation_dataset.csv')
    valid=geo.geolocation_lat.between(-90,90)&geo.geolocation_lng.between(-180,180)
    centers=geo.loc[valid].groupby('geolocation_zip_code_prefix')[['geolocation_lat','geolocation_lng']].median()
    orders=pd.read_csv(raw/'olist_orders_dataset.csv',usecols=['order_id','customer_id'])
    customers=pd.read_csv(raw/'olist_customers_dataset.csv',usecols=['customer_id','customer_zip_code_prefix'])
    sellers=pd.read_csv(raw/'olist_sellers_dataset.csv',usecols=['seller_id','seller_zip_code_prefix'])
    x=df.merge(orders,on='order_id',validate='one_to_one').merge(customers,on='customer_id',validate='many_to_one').merge(sellers,on='seller_id',validate='many_to_one')
    coords=[np.radians(x[f'{who}_zip_code_prefix'].map(centers[c]).to_numpy()) for who in ['customer','seller'] for c in ['geolocation_lat','geolocation_lng']]
    a,b,c,d=coords
    h=np.sin((c-a)/2)**2+np.cos(a)*np.cos(c)*np.sin((d-b)/2)**2
    x['distance_km']=6371*2*np.arcsin(np.sqrt(np.clip(h,0,1)))
    return x


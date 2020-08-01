using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Xamarin.Forms;
using Xamarin.Essentials;

namespace NotTheOnlyOne
{
    // Learn more about making custom code visible in the Xamarin.Forms previewer
    // by visiting https://aka.ms/xamarinforms-previewer
    [DesignTimeVisible(false)]
    public partial class MainPage : ContentPage
    {
        public MainPage()
        {
            InitializeComponent();
        }

        void webviewNavigating(System.Object sender, Xamarin.Forms.WebNavigatingEventArgs e)
        {
            if (!(e.Url.StartsWith("https://test.nottheonlyone.org")))
            {
                if (!(e.Url.StartsWith("https://platform.twitter.com")))
                {
                    try
                    {
                        var uri = new Uri(e.Url);
                        Launcher.OpenAsync(uri);
                    }
                    catch (Exception)
                    {
                    }

                    e.Cancel = true;
                }
            }
        }
    }
}

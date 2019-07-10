<?php
/**
 * Created by PhpStorm.
 * User: ars
 * Date: 09.07.19
 * Time: 14:31
 */

namespace ThoughtBundle\Admin;

use Sonata\AdminBundle\Admin\Admin;
use Sonata\AdminBundle\Datagrid\ListMapper;
use Sonata\AdminBundle\Form\FormMapper;
use ThoughtBundle\Entity\DynamicPage;

class BannerAdmin extends Admin
{
    /**
     * @param FormMapper $formMapper
     */
    protected function configureFormFields(FormMapper $formMapper)
    {
        $formMapper
            ->add('title')
            ->add('content', 'textarea', [
                'attr' => [
                    'class' => 'js-full-ckeditor'
                ],
                'label' => 'Banner text'
            ])
            ->add('page', 'entity', [
                'class' => DynamicPage::class,
                'choice_label' => 'title',
                'required' => false,
                'label' => 'Link to the page'
            ])
            ->add('isActive', 'checkbox', [
                'required' => false
            ])
        ;
    }

    /**
     * @param ListMapper $listMapper
     */
    protected function configureListFields(ListMapper $listMapper)
    {
        $listMapper
            ->addIdentifier('title')
            ->add('page.title')
            ->add('isActive')
        ;
    }

}
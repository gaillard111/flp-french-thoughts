<?php


namespace ThoughtBundle\Admin;


use Sonata\AdminBundle\Admin\Admin;
use Sonata\AdminBundle\Datagrid\ListMapper;
use Sonata\AdminBundle\Form\FormMapper;

class DynamicPageAdmin extends Admin
{
    /**
     * @param ListMapper $listMapper
     */
    protected function configureListFields(ListMapper $listMapper)
    {
        $listMapper
            ->addIdentifier('id')
            ->add('title')
        ;
    }

    protected function configureFormFields(FormMapper $formMapper)
    {
        $formMapper
            ->add('title')
            ->add('slug', 'text', [
                'required' => false
            ])
            ->add('text', 'textarea', [
                'label' => 'Text',
                'attr'  => [
                    'class' => 'js-full-ckeditor'
                ],
            ])

        ;
    }
}
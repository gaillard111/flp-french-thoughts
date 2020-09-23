<?php

namespace AdminBundle\Controller;

use FOS\CKEditorBundle\Form\Type\CKEditorType;
use Sonata\AdminBundle\Admin\AbstractAdmin;
use Sonata\AdminBundle\Datagrid\ListMapper;
use Sonata\AdminBundle\Form\FormMapper;
use Symfony\Component\Form\CallbackTransformer;
use ThoughtBundle\Entity\DynamicPage;

class DynamicPageAdmin extends AbstractAdmin
{
    /**
     * @param ListMapper $listMapper
     */
    protected function configureListFields(ListMapper $listMapper)
    {
        $listMapper
            ->addIdentifier('title')
            ->add('text', 'html', [
                'strip' => true,
                'collapse' => [
                    'height' => 100,
                ]
            ])
        ;
    }

    protected function configureFormFields(FormMapper $formMapper)
    {
        $formMapper
            ->add('title')
            ->add('slug', 'text', [
                'required' => false,
            ])
            ->add('text', CKEditorType::Class, [
                'config'    => [
                    'filebrowserBrowseRoute' => 'ckeditor_image_upload',
                    'extraPlugins' => 'imageuploader'
                ],
            ]);
        ;

        $formMapper->getFormBuilder()->get('slug')->addViewTransformer(new CallbackTransformer(
            function ($slug) {
                return 'page/' . $slug;
            },
            function ($slug) {
                $url_parts = explode('/', $slug);
                if (end($url_parts) != '') {
                    return end($url_parts);
                }
                return null;
            }
        ));
    }

    public function toString($object)
    {
        return $object instanceof DynamicPage
            ? $object->getTitle()
            : 'Page';
    }
}